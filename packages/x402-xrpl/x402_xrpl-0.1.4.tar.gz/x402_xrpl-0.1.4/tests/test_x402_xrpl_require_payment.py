import base64
import json

from fastapi import FastAPI
from starlette.testclient import TestClient

from x402_xrpl.server import require_payment


def test_require_payment_returns_402_with_payment_requirements():
    app = FastAPI()

    app.middleware("http")(
        require_payment(
            path="/weather",
            price="1000",
            pay_to_address="rPAYTO",
            network="xrpl:1",
            facilitator_url="http://example.com",
            resource="demo:weather",
            invoice_id_factory=lambda: "INV123",
        )
    )

    @app.get("/weather")
    def weather():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/weather")

    assert resp.status_code == 402
    body = resp.json()

    assert "PAYMENT-REQUIRED" in resp.headers
    decoded = json.loads(base64.b64decode(resp.headers["PAYMENT-REQUIRED"]))
    assert decoded == body

    assert body["x402Version"] == 2
    assert body["resource"]["url"] == "demo:weather"
    assert isinstance(body.get("accepts"), list) and len(body["accepts"]) == 1
    req = body["accepts"][0]
    assert req["payTo"] == "rPAYTO"
    assert req["amount"] == "1000"
    assert req["asset"] == "XRP"
    assert req["network"] == "xrpl:1"
    assert req["scheme"] == "exact"
    assert req["extra"]["invoiceId"] == "INV123"
    assert req["extra"]["sourceTag"] == 804681468


def test_require_payment_allows_overriding_source_tag():
    app = FastAPI()

    app.middleware("http")(
        require_payment(
            path="/weather",
            price="1000",
            pay_to_address="rPAYTO",
            network="xrpl:1",
            facilitator_url="http://example.com",
            resource="demo:weather",
            invoice_id_factory=lambda: "INV123",
            extra={"sourceTag": 123},
        )
    )

    @app.get("/weather")
    def weather():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/weather")

    assert resp.status_code == 402
    body = resp.json()
    req = body["accepts"][0]
    assert req["extra"]["invoiceId"] == "INV123"
    assert req["extra"]["sourceTag"] == 123

