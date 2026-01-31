from __future__ import annotations

import os
from typing import Any, Callable, Mapping, Sequence

import requests
from xrpl.wallet import Wallet

from x402_xrpl.client import XRPLPresignedPaymentPayer, XRPLPresignedPaymentPayerOptions
from x402_xrpl.clients.base import MaxValue, x402Client
from x402_xrpl.types import PaymentRequirements

PaymentRequirementsSelector = Callable[
    [Sequence[Mapping[str, Any]], str | None, str | None, MaxValue | None],
    Mapping[str, Any],
]
PaymentHeaderFactory = Callable[[PaymentRequirements], str]


def _has_header(headers: Mapping[str, Any], name: str) -> bool:
    target = name.lower()
    return any(str(k).lower() == target for k in headers.keys())


class X402RequestsSession(requests.Session):
    """
    requests.Session wrapper that auto-handles the x402 flow:

    - Make request
    - If 402 + accepts: select reqs, build PAYMENT-SIGNATURE, retry once
    """

    def __init__(
        self,
        wallet: Wallet,
        *,
        rpc_url: str,
        payment_requirements_selector: PaymentRequirementsSelector = x402Client.default_payment_requirements_selector,
        network_filter: str | None = None,
        scheme_filter: str | None = "exact",
        max_value: MaxValue | None = None,
        invoice_binding: str = "both",
        payment_header_factory: PaymentHeaderFactory | None = None,
        x_payment_header: str = "PAYMENT-SIGNATURE",
    ) -> None:
        super().__init__()
        self._wallet = wallet
        self._rpc_url = rpc_url
        self._selector = payment_requirements_selector
        self._network_filter = network_filter
        self._scheme_filter = scheme_filter
        self._max_value = max_value
        self._invoice_binding = invoice_binding
        self._payment_header_factory = payment_header_factory
        self._x_payment_header = x_payment_header

    def _build_x_payment(self, reqs: PaymentRequirements) -> str:
        if self._payment_header_factory is not None:
            return self._payment_header_factory(reqs)

        payer = XRPLPresignedPaymentPayer(
            XRPLPresignedPaymentPayerOptions(
                wallet=self._wallet,
                network=reqs.network,  # type: ignore[arg-type]
                rpc_url=self._rpc_url,
                invoice_binding=self._invoice_binding,  # type: ignore[arg-type]
            )
        )
        return payer.create_payment_header(reqs)

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        headers_in = dict(kwargs.get("headers") or {})
        other_kwargs = {k: v for k, v in kwargs.items() if k != "headers"}

        resp = super().request(method, url, headers=headers_in, **other_kwargs)
        if resp.status_code != 402:
            return resp

        # Don’t override a caller-supplied payment header
        if _has_header(headers_in, self._x_payment_header):
            return resp

        try:
            body = resp.json()
        except Exception:
            return resp
        if not isinstance(body, dict):
            return resp

        accepts: list[Mapping[str, Any]] = []

        raw_accepts = body.get("accepts")
        if isinstance(raw_accepts, list):
            accepts.extend([a for a in raw_accepts if isinstance(a, Mapping)])

        if not accepts:
            return resp

        try:
            selected = self._selector(
                accepts,
                self._network_filter,
                self._scheme_filter,
                self._max_value,
            )
            reqs = PaymentRequirements.from_dict(selected)
            x_payment = self._build_x_payment(reqs)
        except Exception:
            # Fail open: return the original 402 so callers can inspect/handle it.
            return resp

        headers_retry = dict(headers_in)
        headers_retry[self._x_payment_header] = x_payment
        return super().request(method, url, headers=headers_retry, **other_kwargs)


def x402_requests(
    wallet: Wallet,
    *,
    rpc_url: str | None = None,
    payment_requirements_selector: PaymentRequirementsSelector = x402Client.default_payment_requirements_selector,
    network_filter: str | None = None,
    scheme_filter: str | None = "exact",
    max_value: MaxValue | None = None,
    invoice_binding: str = "both",
    payment_header_factory: PaymentHeaderFactory | None = None,
) -> X402RequestsSession:
    """
    Construct a requests.Session that auto-handles x402 on XRPL.

    Typical usage:
      session = x402_requests(wallet, rpc_url=..., network_filter="xrpl:1")
      resp = session.get(url)
    """
    rpc_url = rpc_url or os.getenv("XRPL_RPC_URL") or os.getenv("XRPL_TESTNET_RPC_URL")
    if not rpc_url:
        raise ValueError("rpc_url is required (pass rpc_url=... or set XRPL_RPC_URL)")

    return X402RequestsSession(
        wallet,
        rpc_url=rpc_url,
        payment_requirements_selector=payment_requirements_selector,
        network_filter=network_filter,
        scheme_filter=scheme_filter,
        max_value=max_value,
        invoice_binding=invoice_binding,
        payment_header_factory=payment_header_factory,
    )

