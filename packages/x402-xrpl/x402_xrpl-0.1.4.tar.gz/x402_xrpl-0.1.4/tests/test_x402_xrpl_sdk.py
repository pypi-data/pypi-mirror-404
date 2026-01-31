import base64
import json

from x402_xrpl.types import (
    FacilitatorSupportedResponse,
    PaymentRequired,
    PaymentPayload,
    PaymentRequirements,
    PaymentVerifyResponse,
    ResourceInfo,
    SettlementResponse,
)


def test_payment_requirements_roundtrip():
    wire = {
        "scheme": "exact",
        "network": "xrpl:1",
        "amount": "1000000",
        "asset": "XRP",
        "payTo": "rPAYTO",
        "maxTimeoutSeconds": 600,
        "extra": {"foo": "bar", "invoiceId": "INV123"},
    }
    req = PaymentRequirements.from_dict(wire)

    assert req.scheme == "exact"
    assert req.network == "xrpl:1"
    assert req.amount == "1000000"
    assert req.asset == "XRP"
    assert req.pay_to == "rPAYTO"
    assert req.invoice_id() == "INV123"

    back = req.to_dict()
    assert back == wire


def test_payment_requirements_from_dict_accepts_currency_and_issuer_aliases():
    wire = {
        "scheme": "exact",
        "network": "xrpl:1",
        "amount": "1.5",
        "currency": "524C555344000000000000000000000000000000",
        "issuer": "rISSUER",
        "payTo": "rPAYTO",
        "maxTimeoutSeconds": 600,
        "extra": {"invoiceId": "INV123"},
    }

    req = PaymentRequirements.from_dict(wire)

    assert req.asset == "524C555344000000000000000000000000000000"
    assert req.extra is not None
    assert req.extra.get("issuer") == "rISSUER"
    assert req.extra.get("invoiceId") == "INV123"

    back = req.to_dict()
    assert back["asset"] == "524C555344000000000000000000000000000000"
    assert back["extra"]["issuer"] == "rISSUER"


def test_payment_required_to_dict():
    req = PaymentRequirements(
        scheme="exact",
        network="xrpl:1",
        amount="42",
        asset="XRP",
        pay_to="rPAYTO",
        max_timeout_seconds=60,
        extra={"invoiceId": "INV-XYZ"},
    )
    resp = PaymentRequired(
        x402_version=2,
        error="PAYMENT-SIGNATURE header is required",
        resource=ResourceInfo(url="demo:xrpl", description="desc", mime_type="application/json"),
        accepts=[req],
        extensions={},
    )
    wire = resp.to_dict()

    assert wire["x402Version"] == 2
    assert wire["error"] == "PAYMENT-SIGNATURE header is required"
    assert wire["resource"]["url"] == "demo:xrpl"
    assert len(wire["accepts"]) == 1
    accepts0 = wire["accepts"][0]
    assert accepts0["amount"] == "42"
    assert accepts0["payTo"] == "rPAYTO"
    assert accepts0["extra"]["invoiceId"] == "INV-XYZ"


def test_facilitator_supported_response_from_wire_kinds_and_supported():
    data_kinds = {
        "kinds": [
            {"x402Version": 2, "scheme": "exact", "network": "xrpl:1"},
        ],
        "extensions": [],
        "signers": {"xrpl:*": []},
    }
    resp_kinds = FacilitatorSupportedResponse.from_wire(data_kinds)
    assert len(resp_kinds.kinds) == 1
    assert resp_kinds.kinds[0].scheme == "exact"
    assert resp_kinds.kinds[0].network == "xrpl:1"
    assert resp_kinds.kinds[0].x402_version == 2


def test_payment_verify_response_from_wire():
    data = {"isValid": True, "invalidReason": None, "payer": "0xPAYER"}
    resp = PaymentVerifyResponse.from_wire(data)
    assert resp.is_valid is True
    assert resp.invalid_reason is None
    assert resp.payer == "0xPAYER"


def test_settlement_response_from_wire_spec_shape():
    data = {
        "success": True,
        "transaction": "0xabc",
        "network": "base-sepolia",
        "payer": "0xPAYER",
        "errorReason": None,
    }
    resp = SettlementResponse.from_wire(data)
    assert resp.success is True
    assert resp.transaction == "0xabc"
    assert resp.network == "base-sepolia"
    assert resp.payer == "0xPAYER"
    assert resp.error_reason is None


def test_settlement_response_from_wire_xrpl_shape():
    data = {
        "success": False,
        "errorReason": "verify_failed:auth_out_of_window",
        "transaction": "",
        "network": "xrpl:1",
    }
    resp = SettlementResponse.from_wire(data)
    assert resp.success is False
    assert resp.transaction == ""
    assert resp.network == "xrpl:1"
    assert resp.error_reason == "verify_failed:auth_out_of_window"


def test_payment_payload_encoding_matches_header_envelope_shape():
    req = PaymentRequirements(
        scheme="exact",
        network="xrpl:1",
        amount="1000000",
        asset="XRP",
        pay_to="rPAYTO",
        max_timeout_seconds=600,
        extra={"invoiceId": "INV123"},
    )
    env = PaymentPayload(
        x402_version=2,
        resource=None,
        accepted=req,
        payload={"signedTxBlob": "DEADBEEF", "invoiceId": "INV123"},
        extensions={},
    ).to_dict()
    header = base64.b64encode(
        json.dumps(env, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).decode("utf-8")

    # Ensure the header decodes back to the same envelope
    decoded = json.loads(base64.b64decode(header))
    assert decoded["x402Version"] == 2
    assert decoded["accepted"]["scheme"] == "exact"
    assert decoded["accepted"]["network"] == "xrpl:1"
    assert decoded["payload"]["signedTxBlob"] == "DEADBEEF"
