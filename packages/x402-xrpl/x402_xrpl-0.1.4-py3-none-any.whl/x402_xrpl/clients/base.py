from __future__ import annotations

import base64
import json
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence, Union

MaxValue = Union[str, int, float, Decimal]


def decode_payment_response(header_value: str) -> dict[str, Any]:
    """
    Decode PAYMENT-RESPONSE (base64-encoded JSON) into a dict.
    """
    try:
        raw = base64.b64decode(header_value)
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError("Invalid PAYMENT-RESPONSE (expected base64 JSON)") from exc

    if not isinstance(data, dict):
        raise ValueError("Invalid PAYMENT-RESPONSE (decoded JSON was not an object)")
    return data


def decode_x_payment_response(header_value: str) -> dict[str, Any]:
    """
    Deprecated alias for `decode_payment_response`.
    """
    return decode_payment_response(header_value)


def _to_decimal(v: Any) -> Optional[Decimal]:
    try:
        return Decimal(str(v))
    except Exception:
        return None


class X402Client:
    """
    Buyer-side helpers mirroring the naming style of the upstream x402 Python client.
    """

    @staticmethod
    def default_payment_requirements_selector(
        accepts: Sequence[Mapping[str, Any]],
        network_filter: Optional[str] = None,
        scheme_filter: Optional[str] = None,
        max_value: Optional[MaxValue] = None,
    ) -> Mapping[str, Any]:
        """
        Select a single PaymentRequirements dict from an accepts list.

        Defaults:
        - If no filters are provided, returns the first entry (server ordering wins).
        - If filters are provided, filters down then returns the first remaining entry.
        """
        candidates = list(accepts)

        if network_filter:
            candidates = [a for a in candidates if str(a.get("network", "")) == network_filter]
        if scheme_filter:
            candidates = [a for a in candidates if str(a.get("scheme", "")) == scheme_filter]

        if max_value is not None:
            mv = _to_decimal(max_value)
            if mv is None:
                raise ValueError(f"Invalid max_value: {max_value!r}")
            filtered: list[Mapping[str, Any]] = []
            for a in candidates:
                amt = _to_decimal(a.get("amount"))
                if amt is not None and amt <= mv:
                    filtered.append(a)
            candidates = filtered

        if not candidates:
            raise ValueError(
                "No acceptable payment requirement found "
                f"(network_filter={network_filter!r}, scheme_filter={scheme_filter!r}, "
                f"max_value={max_value!r})"
            )

        return candidates[0]


# Alias to match upstream x402 naming style
x402Client = X402Client

