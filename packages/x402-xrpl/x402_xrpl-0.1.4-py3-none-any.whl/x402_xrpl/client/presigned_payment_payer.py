from __future__ import annotations

import base64
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Literal, Mapping, Optional

from xrpl.clients import JsonRpcClient
from xrpl.ledger import get_latest_validated_ledger_sequence
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import Memo, Payment
from xrpl.transaction import autofill, sign
from xrpl.wallet import Wallet

from x402_xrpl.types import PaymentPayload, PaymentRequirements

InvoiceBindingMode = Literal["memos", "invoice_id", "both"]
XRPLNetworkId = Literal["xrpl:0", "xrpl:1", "xrpl:2"]

DEFAULT_SOURCE_TAG = 804_681_468


def invoice_id_to_memo_hex(invoice_id: str) -> str:
    """
    Encode an invoice id as UTF-8 and return uppercase hex suitable for MemoData.
    """
    return invoice_id.encode("utf-8").hex().upper()


def invoice_id_to_invoice_id_field(invoice_id: str) -> str:
    """
    Encode an invoice id into the XRPL Payment.InvoiceID field as SHA-256(invoice_id).
    """
    return hashlib.sha256(invoice_id.encode("utf-8")).hexdigest().upper()


def build_payment_header_for_signed_blob(
    *,
    req: PaymentRequirements,
    signed_tx_blob: str,
    invoice_id: str,
) -> str:
    """
    Build the base64 JSON envelope for the PAYMENT-SIGNATURE header.
    """
    payment_payload = PaymentPayload(
        x402_version=2,
        resource=None,
        accepted=req,
        payload={"signedTxBlob": signed_tx_blob, "invoiceId": invoice_id},
    )
    return base64.b64encode(
        json.dumps(payment_payload.to_dict(), separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).decode("utf-8")


@dataclass(frozen=True)
class XRPLPresignedPaymentPayerOptions:
    wallet: Wallet
    network: XRPLNetworkId
    rpc_url: str
    invoice_binding: InvoiceBindingMode = "both"


@dataclass(frozen=True)
class XRPLPresignedPreparedPayment:
    payment_payload: PaymentPayload
    payment_header: str
    signed_tx_blob: str
    invoice_id: str


class XRPLPresignedPaymentPayer:
    """
    Client-side helper that:
      - validates PaymentRequirements for XRPL exact presigned payments
      - builds an XRPL Payment transaction (XRP + direct IOU v1)
      - binds invoiceId into the tx (Memos and/or InvoiceID)
      - autofills + signs to a tx blob (hex)
      - returns PAYMENT-SIGNATURE header value (base64 JSON PaymentPayload)
    """

    def __init__(
        self,
        options: XRPLPresignedPaymentPayerOptions,
        *,
        client: Optional[JsonRpcClient] = None,
    ) -> None:
        self._options = options
        self._client = client or JsonRpcClient(options.rpc_url)

    def supports(self, req: PaymentRequirements) -> bool:
        if req.scheme != "exact":
            return False
        if req.network not in ("xrpl:0", "xrpl:1", "xrpl:2"):
            return False
        asset = str(req.asset or "XRP")
        if asset.upper() == "XRP":
            return True
        try:
            to_currency_hex(asset)
        except ValueError:
            return False
        return _issuer_from_payment_req(req) is not None

    def prepare_payment(
        self,
        req: PaymentRequirements,
        *,
        invoice_id: Optional[str] = None,
    ) -> XRPLPresignedPreparedPayment:
        if not self.supports(req):
            raise ValueError("PaymentRequirements not supported by XRPLPresignedPaymentPayer")

        inv = invoice_id or req.invoice_id()
        if not inv:
            raise ValueError('invoice_id is required (expected PaymentRequirements.extra["invoiceId"])')

        memo_list: list[Memo] | None = None
        invoice_id_field: str | None = None

        if self._options.invoice_binding in ("memos", "both"):
            memo_list = [Memo(memo_data=invoice_id_to_memo_hex(inv))]

        if self._options.invoice_binding in ("invoice_id", "both"):
            invoice_id_field = invoice_id_to_invoice_id_field(inv)

        destination_tag: int | None = None
        if isinstance(req.extra, Mapping):
            raw_tag = req.extra.get("destinationTag")
            if raw_tag is not None:
                try:
                    destination_tag = int(raw_tag)
                except Exception as exc:
                    raise ValueError('destinationTag must be an integer (expected PaymentRequirements.extra["destinationTag"])') from exc

        source_tag: int = DEFAULT_SOURCE_TAG
        if isinstance(req.extra, Mapping):
            raw_source_tag = req.extra.get("sourceTag")
            if raw_source_tag is not None:
                try:
                    source_tag = int(raw_source_tag)
                except Exception as exc:
                    raise ValueError('sourceTag must be an integer (expected PaymentRequirements.extra["sourceTag"])') from exc

        asset = str(req.asset or "XRP")
        if asset.upper() == "XRP":
            amount: str | IssuedCurrencyAmount = str(int(req.amount))
            send_max: str | IssuedCurrencyAmount | None = None
        else:
            issuer = _issuer_from_payment_req(req)
            if not issuer:
                raise ValueError('issuer is required for IOU payments (expected PaymentRequirements.extra["issuer"])')
            currency_hex = to_currency_hex(asset)
            amount = IssuedCurrencyAmount(
                currency=currency_hex,
                issuer=issuer,
                value=str(req.amount),
            )
            # IOU policy: include SendMax (same currency+issuer, value >= destination value).
            send_max = IssuedCurrencyAmount(
                currency=currency_hex,
                issuer=issuer,
                value=str(req.amount),
            )

        # Bind maxTimeoutSeconds to LastLedgerSequence (ledger-based expiry).
        current_validated_ledger = get_latest_validated_ledger_sequence(self._client)
        max_ledger_delta = int(math.ceil(int(req.max_timeout_seconds) / 5.0) + 2)
        last_ledger_sequence = int(current_validated_ledger) + max_ledger_delta

        payment_tx = Payment(
            account=self._options.wallet.classic_address,
            destination=req.pay_to,
            amount=amount,
            send_max=send_max,
            memos=memo_list,
            invoice_id=invoice_id_field,
            source_tag=source_tag,
            destination_tag=destination_tag,
            last_ledger_sequence=last_ledger_sequence,
        )

        filled = autofill(payment_tx, self._client)
        signed = sign(filled, self._options.wallet)
        signed_blob = signed.blob()

        payment_payload = PaymentPayload(
            x402_version=2,
            resource=None,
            accepted=req,
            payload={"signedTxBlob": signed_blob, "invoiceId": inv},
        )
        header = base64.b64encode(
            json.dumps(payment_payload.to_dict(), separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).decode("utf-8")

        return XRPLPresignedPreparedPayment(
            payment_payload=payment_payload,
            payment_header=header,
            signed_tx_blob=signed_blob,
            invoice_id=inv,
        )

    def create_payment_header(
        self,
        req: PaymentRequirements,
        *,
        invoice_id: Optional[str] = None,
    ) -> str:
        return self.prepare_payment(req, invoice_id=invoice_id).payment_header


def _issuer_from_payment_req(req: PaymentRequirements) -> Optional[str]:
    extra = req.extra
    if not isinstance(extra, Mapping):
        return None
    issuer = extra.get("issuer")
    if not isinstance(issuer, str) or not issuer:
        return None
    return issuer


def to_currency_hex(code: str) -> str:
    """
    Normalize an XRPL currency code to a valid XRPL JSON representation.

    Accepted inputs:
    - 3-character code (e.g. "USD") → returns uppercase 3-char
    - 40-char hex (160-bit currency code) → returns uppercase 40-hex

    NOTE: Per this repo’s XRPL x402 exact presigned-payment spec, IOU `asset`
    values MUST be either 3-char or 40-hex (do not pass longer strings like
    "RLUSD"; use the 160-bit hex currency code instead).
    """
    code = code.strip()
    if len(code) == 40:
        try:
            bytes.fromhex(code)
            return code.upper()
        except ValueError:
            pass

    if len(code) == 3:
        return code.upper()

    raise ValueError('Invalid XRPL currency code (expected 3 chars or 40-hex).')
