import base64
import hashlib
import json

import x402_xrpl.client.presigned_payment_payer as payer_mod
from xrpl.wallet import Wallet

from x402_xrpl.client.presigned_payment_payer import (
    build_payment_header_for_signed_blob,
    invoice_id_to_invoice_id_field,
    invoice_id_to_memo_hex,
)
from x402_xrpl.types import PaymentRequirements


def test_presigned_invoice_memo_hex_roundtrip():
    invoice_id = "INV-123"
    memo_hex = invoice_id_to_memo_hex(invoice_id)
    assert bytes.fromhex(memo_hex).decode("utf-8") == invoice_id


def test_presigned_invoice_id_field_is_sha256_upper_hex():
    invoice_id = "INV-123"
    expected = hashlib.sha256(invoice_id.encode("utf-8")).hexdigest().upper()
    assert invoice_id_to_invoice_id_field(invoice_id) == expected


def test_presigned_payment_header_envelope_shape():
    req = PaymentRequirements(
        scheme="exact",
        network="xrpl:1",
        amount="1000000",
        asset="XRP",
        pay_to="rPAYTO",
        max_timeout_seconds=600,
        extra={"invoiceId": "INV-123"},
    )

    header = build_payment_header_for_signed_blob(
        req=req,
        signed_tx_blob="DEADBEEF",
        invoice_id=req.invoice_id() or "INV-123",
    )

    decoded = json.loads(base64.b64decode(header))
    assert decoded["x402Version"] == 2
    assert decoded["accepted"]["scheme"] == "exact"
    assert decoded["accepted"]["network"] == "xrpl:1"
    assert decoded["payload"]["signedTxBlob"] == "DEADBEEF"
    assert decoded["payload"]["invoiceId"] == "INV-123"


def test_prepare_payment_sets_default_source_tag(monkeypatch):
    wallet = Wallet.from_seed("sEd7M69Yu4Kz8JkunvshAzrPwwdQYQL")
    captured: dict[str, object] = {}

    def fake_autofill(tx, _client):  # type: ignore[no-untyped-def]
        captured["tx"] = tx
        return tx

    class DummySigned:
        def blob(self) -> str:
            return "DEADBEEF"

    def fake_sign(_tx, _wallet):  # type: ignore[no-untyped-def]
        return DummySigned()

    monkeypatch.setattr(payer_mod, "get_latest_validated_ledger_sequence", lambda _c: 100)
    monkeypatch.setattr(payer_mod, "autofill", fake_autofill)
    monkeypatch.setattr(payer_mod, "sign", fake_sign)

    payer = payer_mod.XRPLPresignedPaymentPayer(
        payer_mod.XRPLPresignedPaymentPayerOptions(
            wallet=wallet,
            network="xrpl:1",
            rpc_url="http://example.com",
        ),
        client=object(),  # avoid network calls
    )

    req = PaymentRequirements(
        scheme="exact",
        network="xrpl:1",
        amount="100",
        asset="XRP",
        pay_to="rPAYTO",
        max_timeout_seconds=600,
        extra={"invoiceId": "INV-123"},
    )

    payer.prepare_payment(req)
    tx = captured["tx"]
    assert getattr(tx, "source_tag") == payer_mod.DEFAULT_SOURCE_TAG


def test_prepare_payment_allows_overriding_source_tag(monkeypatch):
    wallet = Wallet.from_seed("sEd7M69Yu4Kz8JkunvshAzrPwwdQYQL")
    captured: dict[str, object] = {}

    def fake_autofill(tx, _client):  # type: ignore[no-untyped-def]
        captured["tx"] = tx
        return tx

    class DummySigned:
        def blob(self) -> str:
            return "DEADBEEF"

    def fake_sign(_tx, _wallet):  # type: ignore[no-untyped-def]
        return DummySigned()

    monkeypatch.setattr(payer_mod, "get_latest_validated_ledger_sequence", lambda _c: 100)
    monkeypatch.setattr(payer_mod, "autofill", fake_autofill)
    monkeypatch.setattr(payer_mod, "sign", fake_sign)

    payer = payer_mod.XRPLPresignedPaymentPayer(
        payer_mod.XRPLPresignedPaymentPayerOptions(
            wallet=wallet,
            network="xrpl:1",
            rpc_url="http://example.com",
        ),
        client=object(),  # avoid network calls
    )

    req = PaymentRequirements(
        scheme="exact",
        network="xrpl:1",
        amount="100",
        asset="XRP",
        pay_to="rPAYTO",
        max_timeout_seconds=600,
        extra={"invoiceId": "INV-123", "sourceTag": 123},
    )

    payer.prepare_payment(req)
    tx = captured["tx"]
    assert getattr(tx, "source_tag") == 123

