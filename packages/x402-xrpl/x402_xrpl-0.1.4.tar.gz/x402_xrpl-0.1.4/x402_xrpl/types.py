from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping, Optional, Sequence


@dataclass(frozen=True)
class ResourceInfo:
    """
    v2 ResourceInfo describing the protected resource.
    """

    url: str
    description: str | None = None
    mime_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"url": self.url}
        if self.description is not None:
            data["description"] = self.description
        if self.mime_type is not None:
            data["mimeType"] = self.mime_type
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResourceInfo":
        return cls(
            url=str(data["url"]),
            description=str(data["description"]) if data.get("description") is not None else None,
            mime_type=str(data["mimeType"]) if data.get("mimeType") is not None else None,
        )


@dataclass(frozen=True)
class PaymentRequirements:
    """
    v2 PaymentRequirements (scheme/network-specific pricing quote).

    All amounts are strings (uint256-as-string in atomic units).

    XRPL notes (optional conventions):
      - For XRPL IOU payments (non-XRP), the issuer address SHOULD be provided as:
          extra = {"issuer": "<classic address>"}
        because on XRPL an issued currency is uniquely identified by (currency, issuer).

      - For invoice binding in this repo, the server issues an invoice id in:
          extra = {"invoiceId": "<id>"}
    """

    scheme: str
    network: str
    amount: str
    asset: str
    pay_to: str
    max_timeout_seconds: int
    extra: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to v2 wire-format dict using spec field names (camelCase / exact keys).
        """
        data: dict[str, Any] = {
            "scheme": self.scheme,
            "network": self.network,
            "amount": self.amount,
            "asset": self.asset,
            "payTo": self.pay_to,
            "maxTimeoutSeconds": self.max_timeout_seconds,
        }
        if self.extra is not None:
            data["extra"] = dict(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PaymentRequirements":
        """
        Construct from a v2 wire-format dict (e.g., from a 402 or facilitator API).
        """
        # Some clients use "currency" instead of "asset" (XRPL terminology).
        asset = data.get("asset")
        if asset is None:
            asset = data.get("currency")

        extra = data.get("extra")
        # Convenience: accept top-level "issuer" and normalize into extra["issuer"].
        issuer = data.get("issuer")
        if issuer is not None:
            if extra is None:
                extra = {"issuer": issuer}
            elif isinstance(extra, Mapping) and "issuer" not in extra:
                merged: MutableMapping[str, Any] = dict(extra)
                merged["issuer"] = issuer
                extra = merged

        # Convenience: accept top-level invoiceId and normalize into extra["invoiceId"].
        invoice_id = data.get("invoiceId")
        if invoice_id is not None:
            if extra is None:
                extra = {"invoiceId": invoice_id}
            elif isinstance(extra, Mapping) and "invoiceId" not in extra:
                merged = dict(extra)
                merged["invoiceId"] = invoice_id
                extra = merged

        return cls(
            scheme=str(data["scheme"]),
            network=str(data["network"]),
            amount=str(data["amount"]),
            asset=str(asset) if asset is not None else str(data["asset"]),
            pay_to=str(data["payTo"]),
            max_timeout_seconds=int(data["maxTimeoutSeconds"]),
            extra=extra,
        )

    def invoice_id(self) -> str | None:
        extra = self.extra
        if not isinstance(extra, Mapping):
            return None
        invoice_id = extra.get("invoiceId")
        return str(invoice_id) if isinstance(invoice_id, str) and invoice_id else None


@dataclass(frozen=True)
class PaymentPayload:
    """
    v2 PaymentPayload (outer envelope, not base64-encoded).
    """

    x402_version: int
    resource: ResourceInfo | None
    accepted: PaymentRequirements
    payload: Mapping[str, Any]
    extensions: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "x402Version": self.x402_version,
            "accepted": self.accepted.to_dict(),
            "payload": dict(self.payload),
        }
        if self.resource is not None:
            data["resource"] = self.resource.to_dict()
        if self.extensions is not None:
            data["extensions"] = dict(self.extensions)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PaymentPayload":
        resource_raw = data.get("resource")
        resource = ResourceInfo.from_dict(resource_raw) if isinstance(resource_raw, Mapping) else None
        return cls(
            x402_version=int(data["x402Version"]),
            resource=resource,
            accepted=PaymentRequirements.from_dict(data["accepted"]),
            payload=dict(data.get("payload") or {}),
            extensions=dict(data["extensions"]) if isinstance(data.get("extensions"), Mapping) else None,
        )


@dataclass(frozen=True)
class PaymentRequired:
    """
    v2 HTTP 402 PaymentRequired response body.
    """

    x402_version: int
    resource: ResourceInfo
    accepts: Sequence[PaymentRequirements]
    error: str | None = None
    extensions: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "x402Version": self.x402_version,
            "resource": self.resource.to_dict(),
            "accepts": [req.to_dict() for req in self.accepts],
        }
        if self.error is not None:
            data["error"] = self.error
        if self.extensions is not None:
            data["extensions"] = dict(self.extensions)
        else:
            # v2 spec allows optional extensions, but we use {} consistently.
            data["extensions"] = {}
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PaymentRequired":
        return cls(
            x402_version=int(data["x402Version"]),
            resource=ResourceInfo.from_dict(data["resource"]),
            accepts=[PaymentRequirements.from_dict(r) for r in (data.get("accepts") or [])],
            error=str(data["error"]) if data.get("error") is not None else None,
            extensions=dict(data["extensions"]) if isinstance(data.get("extensions"), Mapping) else None,
        )


@dataclass(frozen=True)
class FacilitatorKind:
    """
    Supported (scheme, network) pair with x402 version.
    """

    x402_version: int
    scheme: str
    network: str


@dataclass(frozen=True)
class FacilitatorSupportedResponse:
    """
    Normalized /supported response.

    v2 spec shape includes:
      - kinds: [{x402Version, scheme, network}]
      - extensions: [string]
      - signers: { "<caip2_pattern>": ["addr", ...], ... }
    """

    kinds: Sequence[FacilitatorKind]
    extensions: Sequence[str] = field(default_factory=tuple)
    signers: Mapping[str, Sequence[str]] = field(default_factory=dict)

    @classmethod
    def from_wire(cls, data: Mapping[str, Any]) -> "FacilitatorSupportedResponse":
        kinds_raw: Sequence[Mapping[str, Any]] = []
        raw_kinds = data.get("kinds")
        if isinstance(raw_kinds, list):
            kinds_raw = [k for k in raw_kinds if isinstance(k, Mapping)]

        kinds: list[FacilitatorKind] = []
        for item in kinds_raw:
            kinds.append(
                FacilitatorKind(
                    x402_version=int(item["x402Version"]),
                    scheme=str(item["scheme"]),
                    network=str(item["network"]),
                )
            )
        extensions_raw = data.get("extensions")
        extensions: list[str] = []
        if isinstance(extensions_raw, list):
            extensions = [str(e) for e in extensions_raw]

        signers_raw = data.get("signers")
        signers: dict[str, list[str]] = {}
        if isinstance(signers_raw, Mapping):
            for k, v in signers_raw.items():
                if isinstance(v, list):
                    signers[str(k)] = [str(x) for x in v]
        return cls(kinds=kinds, extensions=extensions, signers=signers)


@dataclass(frozen=True)
class PaymentVerifyResponse:
    """
    Normalized facilitator /verify response.
    """

    is_valid: bool
    invalid_reason: str | None = None
    payer: str | None = None

    @classmethod
    def from_wire(cls, data: Mapping[str, Any]) -> "PaymentVerifyResponse":
        return cls(
            is_valid=bool(data.get("isValid")),
            invalid_reason=data.get("invalidReason"),
            payer=data.get("payer"),
        )


@dataclass(frozen=True)
class SettlementResponse:
    """
    Normalized settlement response per the x402 spec.

    Spec fields:
      - success (bool)
      - errorReason (optional string)
      - transaction (string hash, empty if failed)
      - network (string)
      - payer (optional string)
    """

    success: bool
    transaction: str
    network: str
    payer: str | None = None
    error_reason: str | None = None

    @classmethod
    def from_wire(cls, data: Mapping[str, Any]) -> "SettlementResponse":
        return cls(
            success=bool(data.get("success")),
            transaction=str(data.get("transaction", "")),
            network=str(data.get("network", "")),
            payer=str(data.get("payer")) if data.get("payer") is not None else None,
            error_reason=str(data.get("errorReason")) if data.get("errorReason") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "success": self.success,
            "transaction": self.transaction,
            "network": self.network,
        }
        if self.payer is not None:
            data["payer"] = self.payer
        if self.error_reason is not None:
            data["errorReason"] = self.error_reason
        return data
