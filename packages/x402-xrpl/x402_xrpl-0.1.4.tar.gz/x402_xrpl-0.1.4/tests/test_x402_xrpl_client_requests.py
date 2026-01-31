import base64
import json

import requests
from xrpl.wallet import Wallet

from x402_xrpl.clients.base import decode_payment_response
from x402_xrpl.clients.requests import x402_requests


def test_x402_requests_retries_once_with_payment_signature_header(monkeypatch):
    calls: list[dict] = []

    def fake_request(self, method, url, headers=None, **kwargs):  # noqa: ANN001
        headers = dict(headers or {})
        calls.append({"method": method, "url": url, "headers": headers})

        resp = requests.Response()
        resp.url = url

        if len(calls) == 1:
            resp.status_code = 402
            body = {
                "x402Version": 2,
                "error": "PAYMENT-SIGNATURE header is required",
                "resource": {"url": url, "description": "demo", "mimeType": "application/json"},
                "accepts": [
                    {
                        "scheme": "exact",
                        "network": "xrpl:1",
                        "amount": "1000",
                        "asset": "XRP",
                        "payTo": "rPAYTO",
                        "maxTimeoutSeconds": 600,
                        "extra": {"invoiceId": "INV123"},
                    }
                ],
                "extensions": {},
            }
            resp.headers["Content-Type"] = "application/json"
            resp._content = json.dumps(body).encode("utf-8")
            return resp

        assert headers.get("PAYMENT-SIGNATURE") == "STUB_PAYMENT_HEADER"

        resp.status_code = 200
        resp.headers["Content-Type"] = "application/json"
        resp._content = b'{"ok":true}'

        settlement = {
            "success": True,
            "transaction": "ABC123",
            "network": "xrpl:1",
            "payer": "rPAYER",
        }
        resp.headers["PAYMENT-RESPONSE"] = base64.b64encode(
            json.dumps(settlement, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).decode("utf-8")
        return resp

    monkeypatch.setattr(requests.Session, "request", fake_request)

    wallet = Wallet.from_seed("sEd7M69Yu4Kz8JkunvshAzrPwwdQYQL")
    session = x402_requests(
        wallet,
        rpc_url="http://example-rpc.invalid",
        network_filter="xrpl:1",
        scheme_filter="exact",
        payment_header_factory=lambda _reqs: "STUB_PAYMENT_HEADER",
    )

    resp = session.get("http://example.com/resource", timeout=5)

    assert resp.status_code == 200
    assert len(calls) == 2
    assert "PAYMENT-RESPONSE" in resp.headers

    decoded = decode_payment_response(resp.headers["PAYMENT-RESPONSE"])
    assert decoded["success"] is True
    assert decoded["transaction"] == "ABC123"


def test_x402_requests_does_not_override_existing_payment_signature(monkeypatch):
    calls: list[dict] = []

    def fake_request(self, method, url, headers=None, **kwargs):  # noqa: ANN001
        headers = dict(headers or {})
        calls.append({"method": method, "url": url, "headers": headers})

        resp = requests.Response()
        resp.url = url
        resp.status_code = 402
        resp.headers["Content-Type"] = "application/json"
        resp._content = b'{"x402Version":2,"error":"PAYMENT-SIGNATURE required","resource":{"url":"demo"},"accepts":[],"extensions":{}}'
        return resp

    monkeypatch.setattr(requests.Session, "request", fake_request)

    wallet = Wallet.from_seed("sEd7M69Yu4Kz8JkunvshAzrPwwdQYQL")
    session = x402_requests(
        wallet,
        rpc_url="http://example-rpc.invalid",
        payment_header_factory=lambda _reqs: "STUB_PAYMENT_HEADER",
    )

    resp = session.get(
        "http://example.com/resource",
        headers={"PAYMENT-SIGNATURE": "CALLER_SUPPLIED"},
        timeout=5,
    )

    assert resp.status_code == 402
    assert len(calls) == 1

