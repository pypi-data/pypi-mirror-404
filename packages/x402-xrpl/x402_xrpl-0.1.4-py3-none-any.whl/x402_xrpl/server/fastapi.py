from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping, Optional, Protocol, Sequence

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from x402_xrpl.facilitator import AsyncFacilitatorClient, FacilitatorClientOptions
from x402_xrpl.types import PaymentPayload, PaymentRequired, PaymentRequirements, ResourceInfo

XRPLNetworkId = str

DEFAULT_SOURCE_TAG = 804_681_468


class InvoiceStore(Protocol):
    """
    Minimal persistence contract to bind an issued invoice to its PaymentRequirements.
    (Use Redis/DB in production; memory store is fine for dev.)
    """

    async def put(
        self,
        invoice_id: str,
        reqs: Sequence[PaymentRequirements],
        *,
        ttl_seconds: int,
    ) -> None: ...

    async def get(self, invoice_id: str) -> Optional[Sequence[PaymentRequirements]]: ...

    async def consume(self, invoice_id: str) -> None: ...


@dataclass(frozen=True)
class RequireX402PaymentOption:
    """
    One accepted payment option for an x402-protected resource.

    XRPL notes:
      - For IOUs (asset != "XRP"), issuer MUST be provided (or via extra["issuer"]).
      - max_amount_required is a string:
          - XRP: drops string
          - IOU: issued-currency "value" string
    """

    asset: str
    amount: str
    issuer: Optional[str] = None
    extra: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class RequireX402Options:
    # required pricing fields (x402 PaymentRequirements)
    pay_to: str
    amount: str  # XRP: drops string; IOUs: XRPL issued-currency "value" string
    scheme: str = "exact"
    network: XRPLNetworkId = "xrpl:1"
    asset: str = "XRP"
    issuer: Optional[str] = None  # required for XRPL IOU assets (non-XRP)
    max_timeout_seconds: int = 600

    # resource metadata (recommended by spec)
    resource: Optional[str] = None  # default: request.url
    description: str = ""
    mime_type: str = "application/json"
    output_schema: Optional[dict[str, Any]] = None
    extra: Optional[Mapping[str, Any]] = None
    payment_options: Optional[Sequence[RequireX402PaymentOption]] = None

    # where to settle/verify
    facilitator: Optional[AsyncFacilitatorClient] = None
    facilitator_url: Optional[str] = None  # convenience constructor
    facilitator_headers: Optional[Mapping[str, str]] = None

    # routing
    path: Optional[str | Sequence[str]] = None  # protect all if None

    # invoice binding
    invoice_store: Optional[InvoiceStore] = None
    invoice_ttl_seconds: int = 900
    invoice_id_factory: Optional[Callable[[], str]] = None

    # settlement strategy
    settle: bool = True  # verify only if False (still spec-compatible)


class _InMemoryInvoiceStore:
    def __init__(self) -> None:
        self._data: dict[str, Sequence[PaymentRequirements]] = {}

    async def put(
        self,
        invoice_id: str,
        reqs: Sequence[PaymentRequirements],
        *,
        ttl_seconds: int,  # noqa: ARG002
    ) -> None:
        self._data[invoice_id] = reqs

    async def get(self, invoice_id: str) -> Optional[Sequence[PaymentRequirements]]:
        return self._data.get(invoice_id)

    async def consume(self, invoice_id: str) -> None:
        self._data.pop(invoice_id, None)


def _normalize_paths(path: Optional[str | Sequence[str]]) -> Optional[set[str]]:
    if path is None:
        return None
    if isinstance(path, str):
        return {path}
    return set(path)


def require_x402(
    options: RequireX402Options,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """
    FastAPI/Starlette middleware implementing the x402 flow:
      - If no PAYMENT-SIGNATURE: returns 402 Payment Required with v2 PaymentRequired body.
      - If PAYMENT-SIGNATURE present: calls facilitator /verify (and /settle if enabled) using
        v2 `{ paymentPayload, paymentRequirements }` body.
      - On success: forwards request to handler and sets PAYMENT-RESPONSE header
        containing base64-encoded Settlement Response JSON.
    """

    protected_paths = _normalize_paths(options.path)
    invoice_store: InvoiceStore = options.invoice_store or _InMemoryInvoiceStore()

    if options.facilitator is not None:
        facilitator = options.facilitator
    elif options.facilitator_url is not None:
        facilitator = AsyncFacilitatorClient(
            FacilitatorClientOptions(
                base_url=options.facilitator_url,
            ),
            headers=options.facilitator_headers,
        )
    else:
        raise ValueError("RequireX402Options.facilitator or facilitator_url must be provided")

    async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Pass through CORS preflight requests so CORSMiddleware can handle them
        if request.method == "OPTIONS":
            return await call_next(request)
        if protected_paths is not None and request.url.path not in protected_paths:
            return await call_next(request)

        payment_signature = request.headers.get("PAYMENT-SIGNATURE")
        if not payment_signature:
            invoice_id = options.invoice_id_factory() if options.invoice_id_factory else uuid.uuid4().hex.upper()

            option_specs = options.payment_options
            if not option_specs:
                option_specs = [
                    RequireX402PaymentOption(
                        asset=options.asset,
                        amount=options.amount,
                        issuer=options.issuer,
                        extra=options.extra,
                    )
                ]

            reqs: list[PaymentRequirements] = []
            for opt in option_specs:
                extra: dict[str, Any] | None = dict(options.extra) if options.extra else None
                if opt.extra:
                    extra = dict(extra or {})
                    extra.update(opt.extra)

                issuer = opt.issuer or options.issuer
                if issuer:
                    extra = dict(extra or {})
                    extra["issuer"] = issuer

                # v2: invoice id is carried in extra (and echoed in the scheme payload).
                extra = dict(extra or {})
                # XRPL analytics tag (payer-side, must be set before signing).
                if extra.get("sourceTag") is None:
                    extra["sourceTag"] = DEFAULT_SOURCE_TAG
                extra["invoiceId"] = invoice_id

                reqs.append(
                    PaymentRequirements(
                        scheme=options.scheme,
                        network=options.network,
                        amount=opt.amount,
                        asset=opt.asset,
                        pay_to=options.pay_to,
                        max_timeout_seconds=options.max_timeout_seconds,
                        extra=extra,
                    )
                )

            await invoice_store.put(invoice_id, reqs, ttl_seconds=options.invoice_ttl_seconds)

            resource_url = options.resource or str(request.url)
            body = PaymentRequired(
                x402_version=2,
                error="PAYMENT-SIGNATURE header is required",
                resource=ResourceInfo(url=resource_url, description=options.description, mime_type=options.mime_type),
                accepts=reqs,
                extensions={},
            ).to_dict()
            resp = JSONResponse(status_code=402, content=body)
            resp.headers["PAYMENT-REQUIRED"] = base64.b64encode(
                json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
            ).decode("utf-8")
            return resp

        # Decode envelope so we can recover invoice_id for lookup
        try:
            decoded_raw = json.loads(base64.b64decode(payment_signature))
        except Exception as exc:  # pragma: no cover - defensive
            return JSONResponse(
                status_code=400,
                content={"error": f"invalid_payment_signature_header:{exc}"},
            )

        if not isinstance(decoded_raw, dict):
            return JSONResponse(status_code=400, content={"error": "invalid_payment_signature_header"})

        try:
            payment_payload = PaymentPayload.from_dict(decoded_raw)
        except Exception as exc:  # pragma: no cover - defensive
            return JSONResponse(status_code=400, content={"error": f"invalid_payment_payload:{exc}"})

        if payment_payload.x402_version != 2:
            return JSONResponse(status_code=400, content={"error": "invalid_x402_version"})

        invoice_id = payment_payload.payload.get("invoiceId") if isinstance(payment_payload.payload, dict) else None
        if not invoice_id:
            return JSONResponse(status_code=400, content={"error": "missing_invoiceId"})

        stored = await invoice_store.get(invoice_id)
        if not stored:
            return JSONResponse(status_code=400, content={"error": "unknown_invoice_id"})

        stored_reqs = list(stored)
        selected_req: PaymentRequirements | None = None
        accepted = payment_payload.accepted
        for req in stored_reqs:
            if (
                req.scheme == accepted.scheme
                and req.network == accepted.network
                and req.amount == accepted.amount
                and req.asset == accepted.asset
                and req.pay_to == accepted.pay_to
                and req.max_timeout_seconds == accepted.max_timeout_seconds
                and req.invoice_id() == accepted.invoice_id()
            ):
                selected_req = req
                break

        if not selected_req:
            return JSONResponse(status_code=402, content={"error": "payment_requirements_mismatch"})

        verify_body = {
            "paymentPayload": payment_payload.to_dict(),
            "paymentRequirements": selected_req.to_dict(),
        }
        verify_resp = await facilitator._client.post("/verify", json=verify_body)  # type: ignore[attr-defined]
        if verify_resp.status_code != 200:
            return JSONResponse(
                status_code=502,
                content={"error": f"verify_http_error:{verify_resp.status_code}"},
            )
        verify_json = verify_resp.json()
        if not verify_json.get("isValid"):
            # Re-issue PaymentRequired so clients can retry with a new payment.
            resource_url = options.resource or str(request.url)
            body = PaymentRequired(
                x402_version=2,
                error=f"verify_failed:{verify_json.get('invalidReason')}",
                resource=ResourceInfo(url=resource_url, description=options.description, mime_type=options.mime_type),
                accepts=stored_reqs,
                extensions={},
            ).to_dict()
            resp = JSONResponse(status_code=402, content=body)
            resp.headers["PAYMENT-REQUIRED"] = base64.b64encode(
                json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
            ).decode("utf-8")
            return resp

        if options.settle:
            settle_body = {
                "paymentPayload": payment_payload.to_dict(),
                "paymentRequirements": selected_req.to_dict(),
            }
            settle_resp = await facilitator._client.post("/settle", json=settle_body)  # type: ignore[attr-defined]
            if settle_resp.status_code != 200:
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": f"settle_http_error:{settle_resp.status_code}",
                    },
                )
            settle_json = settle_resp.json()
            if not settle_json.get("success"):
                resource_url = options.resource or str(request.url)
                body = PaymentRequired(
                    x402_version=2,
                    error=f"settle_failed:{settle_json.get('errorReason')}",
                    resource=ResourceInfo(url=resource_url, description=options.description, mime_type=options.mime_type),
                    accepts=stored_reqs,
                    extensions={},
                ).to_dict()
                resp = JSONResponse(status_code=402, content=body)
                resp.headers["PAYMENT-REQUIRED"] = base64.b64encode(
                    json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
                ).decode("utf-8")
                return resp

            await invoice_store.consume(invoice_id)

            inner_response = await call_next(request)
            if "PAYMENT-RESPONSE" in settle_resp.headers:
                inner_response.headers["PAYMENT-RESPONSE"] = settle_resp.headers["PAYMENT-RESPONSE"]
            return inner_response

        # verify-only mode: forward on success without calling /settle
        return await call_next(request)

    return middleware


def require_payment(
    *,
    path: Optional[str | Sequence[str]] = None,
    price: str | int,
    pay_to_address: str,
    network: XRPLNetworkId = "xrpl:1",
    facilitator_url: str | None = None,
    facilitator: AsyncFacilitatorClient | None = None,
    facilitator_headers: Mapping[str, str] | None = None,
    asset: str = "XRP",
    issuer: str | None = None,
    scheme: str = "exact",
    max_timeout_seconds: int = 600,
    resource: str | None = None,
    description: str = "",
    mime_type: str = "application/json",
    output_schema: Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
    payment_options: Sequence[RequireX402PaymentOption] | None = None,
    invoice_store: InvoiceStore | None = None,
    invoice_ttl_seconds: int = 900,
    invoice_id_factory: Callable[[], str] | None = None,
    settle: bool = True,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """
    Ergonomic wrapper around require_x402(...) using XRPL-style inputs.

    Notes:
      - `path` is currently exact-match only (no wildcards/globs).
      - `price` is:
          - XRP: drops string/int (1 XRP = 1_000_000 drops)
          - IOU: issued-currency value string (e.g. "1", "1.25")
      - For IOUs (asset != "XRP"), `issuer` must be provided (or via extra["issuer"]).
    """
    options = RequireX402Options(
        pay_to=pay_to_address,
        amount=str(price),
        scheme=scheme,
        network=network,
        asset=asset,
        issuer=issuer,
        max_timeout_seconds=max_timeout_seconds,
        resource=resource,
        description=description,
        mime_type=mime_type,
        output_schema=dict(output_schema) if output_schema is not None else None,
        extra=extra,
        payment_options=payment_options,
        facilitator=facilitator,
        facilitator_url=facilitator_url,
        facilitator_headers=facilitator_headers,
        path=path,
        invoice_store=invoice_store,
        invoice_ttl_seconds=invoice_ttl_seconds,
        invoice_id_factory=invoice_id_factory,
        settle=settle,
    )
    return require_x402(options)
