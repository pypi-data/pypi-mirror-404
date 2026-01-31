import hashlib

from xrpl.models.transactions import Memo, Payment
from xrpl.transaction import sign
from xrpl.wallet import Wallet

from app.services.xrpl_x402_presigned_payment_facilitator import (
    PaymentPayload,
    PaymentRequirements as FacilitatorPaymentRequirements,
    verify_logic,
)


SENDER_SEED = "sEd7M69Yu4Kz8JkunvshAzrPwwdQYQL"
RECEIVER_SEED = "sEd73youjTvFdc6koXuxMac5ppmse6e"
RLUSD_HEX = "524C555344000000000000000000000000000000"
DEFAULT_SOURCE_TAG = 804681468


def _memo_hex(invoice_id: str) -> str:
    return invoice_id.encode("utf-8").hex().upper()


def _invoice_id_field(invoice_id: str) -> str:
    return hashlib.sha256(invoice_id.encode("utf-8")).hexdigest().upper()


def _to_currency_hex(code: str) -> str:
    if len(code) == 40:
        try:
            bytes.fromhex(code)
            return code.upper()
        except ValueError:
            pass
    if len(code) <= 3:
        return code.upper()
    raw = code.encode("utf-8")
    if len(raw) > 20:
        raise ValueError("Currency code too long (max 20 bytes).")
    return raw.hex().upper().ljust(40, "0")


def _sign_payment_blob(
    *,
    sender: Wallet,
    destination: str,
    amount_drops: int,
    invoice_id: str,
    include_memo: bool = True,
    include_invoice_id_field: bool = False,
    source_tag: int | None = DEFAULT_SOURCE_TAG,
    destination_tag: int | None = None,
    last_ledger_sequence: int | None = 10,
    fee_drops: str = "12",
    flags: int | None = None,
    send_max: object | None = None,
) -> str:
    memos = [Memo(memo_data=_memo_hex(invoice_id))] if include_memo else None
    invoice_id_val = _invoice_id_field(invoice_id) if include_invoice_id_field else None

    tx_kwargs: dict = {
        "account": sender.classic_address,
        "destination": destination,
        "amount": str(int(amount_drops)),
        "sequence": 1,
        "fee": fee_drops,
        "memos": memos,
        "invoice_id": invoice_id_val,
        "flags": flags,
        "send_max": send_max,
    }
    if source_tag is not None:
        tx_kwargs["source_tag"] = source_tag
    if destination_tag is not None:
        tx_kwargs["destination_tag"] = destination_tag
    if last_ledger_sequence is not None:
        tx_kwargs["last_ledger_sequence"] = last_ledger_sequence

    tx = Payment(**tx_kwargs)
    signed = sign(tx, sender)
    return signed.blob()


def _sign_payment_blob_iou(
    *,
    sender: Wallet,
    destination: str,
    currency: str,
    issuer: str,
    value: str,
    invoice_id: str,
    include_memo: bool = True,
    include_invoice_id_field: bool = False,
    include_send_max: bool = True,
    source_tag: int | None = DEFAULT_SOURCE_TAG,
    destination_tag: int | None = None,
    last_ledger_sequence: int | None = 10,
    fee_drops: str = "12",
    flags: int | None = None,
    send_max: object | None = None,
) -> str:
    memos = [Memo(memo_data=_memo_hex(invoice_id))] if include_memo else None
    invoice_id_val = _invoice_id_field(invoice_id) if include_invoice_id_field else None

    amount_obj = {"currency": _to_currency_hex(currency), "issuer": issuer, "value": value}
    if include_send_max and send_max is None:
        send_max = dict(amount_obj)

    tx_kwargs: dict = {
        "account": sender.classic_address,
        "destination": destination,
        "amount": amount_obj,
        "sequence": 1,
        "fee": fee_drops,
        "memos": memos,
        "invoice_id": invoice_id_val,
        "flags": flags,
        "send_max": send_max,
    }
    if source_tag is not None:
        tx_kwargs["source_tag"] = source_tag
    if destination_tag is not None:
        tx_kwargs["destination_tag"] = destination_tag
    if last_ledger_sequence is not None:
        tx_kwargs["last_ledger_sequence"] = last_ledger_sequence

    tx = Payment(**tx_kwargs)
    signed = sign(tx, sender)
    return signed.blob()


def test_verify_valid_memos_binding():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=True,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, payer = verify_logic(payment_payload, req)
    assert ok is True
    assert reason is None
    assert payer == sender.classic_address


def test_verify_accepts_delivermax_when_amount_absent(monkeypatch):
    import app.services.xrpl_x402_presigned_payment_facilitator as facilitator_mod

    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-DM-123"

    tx_json = {
        "TransactionType": "Payment",
        "Account": sender.classic_address,
        "Destination": receiver.classic_address,
        "DeliverMax": "100",
        "LastLedgerSequence": 10,
        "SourceTag": DEFAULT_SOURCE_TAG,
        "Memos": [{"Memo": {"MemoData": _memo_hex(invoice_id)}}],
        "Fee": "12",
    }
    monkeypatch.setattr(facilitator_mod, "xrpl_decode", lambda _blob: tx_json)

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )
    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": "DEADBEEF", "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, payer = verify_logic(payment_payload, req)
    assert ok is True
    assert reason is None
    assert payer == sender.classic_address


def test_verify_rejects_delivermax_and_amount_both_present(monkeypatch):
    import app.services.xrpl_x402_presigned_payment_facilitator as facilitator_mod

    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-DM-AMBIG"

    tx_json = {
        "TransactionType": "Payment",
        "Account": sender.classic_address,
        "Destination": receiver.classic_address,
        "DeliverMax": "100",
        "Amount": "100",
        "LastLedgerSequence": 10,
        "SourceTag": DEFAULT_SOURCE_TAG,
        "Memos": [{"Memo": {"MemoData": _memo_hex(invoice_id)}}],
        "Fee": "12",
    }
    monkeypatch.setattr(facilitator_mod, "xrpl_decode", lambda _blob: tx_json)

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )
    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": "DEADBEEF", "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "amount_mismatch"


def test_verify_rejects_network_id_field_on_standard_network(monkeypatch):
    import app.services.xrpl_x402_presigned_payment_facilitator as facilitator_mod

    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-NID-STD"

    tx_json = {
        "TransactionType": "Payment",
        "Account": sender.classic_address,
        "Destination": receiver.classic_address,
        "Amount": "100",
        "LastLedgerSequence": 10,
        "NetworkID": 1,
        "SourceTag": DEFAULT_SOURCE_TAG,
        "Memos": [{"Memo": {"MemoData": _memo_hex(invoice_id)}}],
        "Fee": "12",
    }
    monkeypatch.setattr(facilitator_mod, "xrpl_decode", lambda _blob: tx_json)

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )
    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": "DEADBEEF", "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "network_id_field_invalid"


def test_verify_rejects_missing_network_id_on_parallel_network(monkeypatch):
    import app.services.xrpl_x402_presigned_payment_facilitator as facilitator_mod

    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-NID-PAR"

    # Allow this network for the duration of the test.
    monkeypatch.setattr(facilitator_mod, "SUPPORTED_NETWORKS", {"xrpl:1025"})

    tx_json = {
        "TransactionType": "Payment",
        "Account": sender.classic_address,
        "Destination": receiver.classic_address,
        "Amount": "100",
        "LastLedgerSequence": 10,
        "SourceTag": DEFAULT_SOURCE_TAG,
        "Memos": [{"Memo": {"MemoData": _memo_hex(invoice_id)}}],
        "Fee": "12",
    }
    monkeypatch.setattr(facilitator_mod, "xrpl_decode", lambda _blob: tx_json)

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1025",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )
    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": "DEADBEEF", "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "network_id_field_invalid"


def test_verify_rejects_destination_tag_mismatch():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-DTAG-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=10,
        destination_tag=123,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id, "destinationTag": 124},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "destination_tag_mismatch"


def test_verify_rejects_source_tag_mismatch():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-STAG-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=10,
        source_tag=DEFAULT_SOURCE_TAG + 1,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id, "sourceTag": DEFAULT_SOURCE_TAG},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "source_tag_mismatch"


def test_verify_rejects_missing_source_tag():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-STAG-MISSING"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=10,
        source_tag=None,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "source_tag_mismatch"


def test_verify_rejects_iou_missing_sendmax():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-IOU-SM-123"

    issuer = sender.classic_address
    blob = _sign_payment_blob_iou(
        sender=sender,
        destination=receiver.classic_address,
        currency=RLUSD_HEX,
        issuer=issuer,
        value="1",
        invoice_id=invoice_id,
        include_memo=True,
        include_send_max=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="1",
        scheme="exact",
        network="xrpl:1",
        asset=RLUSD_HEX,
        maxTimeoutSeconds=600,
        extra={"issuer": issuer, "invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "unsupported_payment_features"


def test_verify_rejects_iou_invalid_asset_format():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-IOU-ASSETFMT"

    issuer = sender.classic_address
    blob = _sign_payment_blob_iou(
        sender=sender,
        destination=receiver.classic_address,
        currency=RLUSD_HEX,
        issuer=issuer,
        value="1",
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="1",
        scheme="exact",
        network="xrpl:1",
        asset="RLUSD",
        maxTimeoutSeconds=600,
        extra={"issuer": issuer, "invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "invalid_payment_requirements"


def test_verify_valid_invoice_id_field_binding():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=False,
        include_invoice_id_field=True,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, payer = verify_logic(payment_payload, req)
    assert ok is True
    assert reason is None
    assert payer == sender.classic_address


def test_verify_rejects_invalid_tx_blob():
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": "NOTHEX", "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "invalid_tx_blob"
    assert payer is None


def test_verify_rejects_missing_last_ledger_sequence():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=None,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "missing_last_ledger_sequence"


def test_verify_rejects_invoice_binding_missing():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=False,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "invoice_binding_missing"


def test_verify_rejects_invoice_binding_mismatch():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    expected_invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id="INV-OTHER",
        include_memo=True,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": expected_invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": expected_invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "invoice_binding_mismatch"


def test_verify_rejects_amount_mismatch():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=200,
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "amount_mismatch"


def test_verify_rejects_sendmax():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=10,
        send_max={"currency": "USD", "issuer": sender.classic_address, "value": "100"},
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "unsupported_payment_features"


def test_verify_rejects_fee_too_high():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-123"

    blob = _sign_payment_blob(
        sender=sender,
        destination=receiver.classic_address,
        amount_drops=100,
        invoice_id=invoice_id,
        include_memo=True,
        last_ledger_sequence=10,
        fee_drops="5001",
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="100",
        scheme="exact",
        network="xrpl:1",
        asset="XRP",
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "fee_too_high"


def test_verify_valid_iou_memos_binding():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-IOU-123"

    issuer = sender.classic_address
    blob = _sign_payment_blob_iou(
        sender=sender,
        destination=receiver.classic_address,
        currency=RLUSD_HEX,
        issuer=issuer,
        value="1",
        invoice_id=invoice_id,
        include_memo=True,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="1.0",
        scheme="exact",
        network="xrpl:1",
        asset=RLUSD_HEX,
        maxTimeoutSeconds=600,
        extra={"issuer": issuer, "invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, payer = verify_logic(payment_payload, req)
    assert ok is True
    assert reason is None
    assert payer == sender.classic_address


def test_verify_rejects_iou_missing_issuer_in_requirements():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-IOU-123"

    blob = _sign_payment_blob_iou(
        sender=sender,
        destination=receiver.classic_address,
        currency=RLUSD_HEX,
        issuer=sender.classic_address,
        value="1",
        invoice_id=invoice_id,
        include_memo=True,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="1",
        scheme="exact",
        network="xrpl:1",
        asset=RLUSD_HEX,
        maxTimeoutSeconds=600,
        extra={"invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "missing_issuer"


def test_verify_rejects_iou_currency_mismatch():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-IOU-123"

    issuer = sender.classic_address
    blob = _sign_payment_blob_iou(
        sender=sender,
        destination=receiver.classic_address,
        currency=RLUSD_HEX,
        issuer=issuer,
        value="1",
        invoice_id=invoice_id,
        include_memo=True,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="1",
        scheme="exact",
        network="xrpl:1",
        asset="USD",
        maxTimeoutSeconds=600,
        extra={"issuer": issuer, "invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "currency_mismatch"


def test_verify_rejects_iou_issuer_mismatch():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-IOU-123"

    blob = _sign_payment_blob_iou(
        sender=sender,
        destination=receiver.classic_address,
        currency=RLUSD_HEX,
        issuer=sender.classic_address,
        value="1",
        invoice_id=invoice_id,
        include_memo=True,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="1",
        scheme="exact",
        network="xrpl:1",
        asset=RLUSD_HEX,
        maxTimeoutSeconds=600,
        extra={"issuer": receiver.classic_address, "invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "issuer_mismatch"


def test_verify_rejects_iou_amount_mismatch():
    sender = Wallet.from_seed(SENDER_SEED)
    receiver = Wallet.from_seed(RECEIVER_SEED)
    invoice_id = "INV-IOU-123"

    issuer = sender.classic_address
    blob = _sign_payment_blob_iou(
        sender=sender,
        destination=receiver.classic_address,
        currency=RLUSD_HEX,
        issuer=issuer,
        value="2",
        invoice_id=invoice_id,
        include_memo=True,
        include_invoice_id_field=False,
        last_ledger_sequence=10,
    )

    req = FacilitatorPaymentRequirements(
        payTo=receiver.classic_address,
        amount="1",
        scheme="exact",
        network="xrpl:1",
        asset=RLUSD_HEX,
        maxTimeoutSeconds=600,
        extra={"issuer": issuer, "invoiceId": invoice_id},
    )

    payment_payload = PaymentPayload(
        accepted=req,
        payload={"signedTxBlob": blob, "invoiceId": invoice_id},
        extensions={},
    )

    ok, reason, _payer = verify_logic(payment_payload, req)
    assert ok is False
    assert reason == "amount_mismatch"
