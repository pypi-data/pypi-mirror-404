from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import httpx

from .types import (
    FacilitatorSupportedResponse,
    PaymentPayload,
    PaymentRequirements,
    PaymentVerifyResponse,
    SettlementResponse,
)


@dataclass(frozen=True)
class FacilitatorClientOptions:
    base_url: str
    timeout_seconds: float = 30.0


class FacilitatorClient:
    """
    Synchronous facilitator client (good for scripts/tools).

    For FastAPI middleware, prefer AsyncFacilitatorClient to avoid blocking
    the event loop.
    """

    def __init__(
        self,
        options: FacilitatorClientOptions,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._options = options
        self._headers = dict(headers or {})

    @staticmethod
    def _decode_payment_header(payment_header: str) -> PaymentPayload:
        decoded = base64.b64decode(payment_header)
        envelope = json.loads(decoded)
        if not isinstance(envelope, dict):
            raise ValueError("Invalid PAYMENT-SIGNATURE header (decoded JSON was not an object)")
        payload = PaymentPayload.from_dict(envelope)
        if payload.x402_version != 2:
            raise ValueError("Invalid PAYMENT-SIGNATURE header (expected x402Version=2)")
        return payload

    def supported(self, *, x402_version: int = 2) -> FacilitatorSupportedResponse:  # noqa: ARG002
        """
        Calls GET /supported and returns supported (scheme, network) pairs.
        """
        url = self._options.base_url.rstrip("/") + "/supported"
        resp = httpx.get(url, headers=self._headers, timeout=self._options.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        return FacilitatorSupportedResponse.from_wire(data)

    def verify(
        self,
        *,
        payment_header: str,
        payment_requirements: PaymentRequirements,
        x402_version: int = 2,  # noqa: ARG002
    ) -> PaymentVerifyResponse:
        """
        POST /verify using v2 `{ paymentPayload, paymentRequirements }`.

        `payment_header` is the base64 JSON value of the `PAYMENT-SIGNATURE` header.
        """
        url = self._options.base_url.rstrip("/") + "/verify"
        payment_payload = self._decode_payment_header(payment_header)
        body = {
            "paymentPayload": payment_payload.to_dict(),
            "paymentRequirements": payment_requirements.to_dict(),
        }
        resp = httpx.post(
            url,
            json=body,
            headers=self._headers,
            timeout=self._options.timeout_seconds,
        )
        resp.raise_for_status()
        return PaymentVerifyResponse.from_wire(resp.json())

    def settle(
        self,
        *,
        payment_header: str,
        payment_requirements: PaymentRequirements,
        x402_version: int = 2,  # noqa: ARG002
    ) -> SettlementResponse:
        """
        POST /settle.
        """
        url = self._options.base_url.rstrip("/") + "/settle"
        payment_payload = self._decode_payment_header(payment_header)
        body = {
            "paymentPayload": payment_payload.to_dict(),
            "paymentRequirements": payment_requirements.to_dict(),
        }
        resp = httpx.post(
            url,
            json=body,
            headers=self._headers,
            timeout=self._options.timeout_seconds,
        )
        resp.raise_for_status()
        return SettlementResponse.from_wire(resp.json())


class AsyncFacilitatorClient:
    """
    Async facilitator client suitable for FastAPI/Starlette middleware.
    """

    def __init__(
        self,
        options: FacilitatorClientOptions,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._options = options
        self._headers = dict(headers or {})
        self._client = httpx.AsyncClient(
            base_url=options.base_url.rstrip("/"),
            headers=self._headers,
            timeout=options.timeout_seconds,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def supported(self, *, x402_version: int = 2) -> FacilitatorSupportedResponse:  # noqa: ARG002
        resp = await self._client.get("/supported")
        resp.raise_for_status()
        return FacilitatorSupportedResponse.from_wire(resp.json())

    async def verify(
        self,
        *,
        payment_header: str,
        payment_requirements: PaymentRequirements,
        x402_version: int = 2,  # noqa: ARG002
    ) -> PaymentVerifyResponse:
        payment_payload = FacilitatorClient._decode_payment_header(payment_header)
        shaped = {
            "paymentPayload": payment_payload.to_dict(),
            "paymentRequirements": payment_requirements.to_dict(),
        }
        resp = await self._client.post("/verify", json=shaped)
        resp.raise_for_status()
        return PaymentVerifyResponse.from_wire(resp.json())

    async def settle(
        self,
        *,
        payment_header: str,
        payment_requirements: PaymentRequirements,
        x402_version: int = 2,  # noqa: ARG002
    ) -> SettlementResponse:
        payment_payload = FacilitatorClient._decode_payment_header(payment_header)
        shaped = {
            "paymentPayload": payment_payload.to_dict(),
            "paymentRequirements": payment_requirements.to_dict(),
        }
        resp = await self._client.post("/settle", json=shaped)
        resp.raise_for_status()
        return SettlementResponse.from_wire(resp.json())


