import base64
import json
import os
import sys
import time
from decimal import Decimal
from pathlib import Path

import requests
from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountLines
from xrpl.models.transactions import Payment, TrustSet
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet

# Ensure project root is on sys.path so x402_xrpl is importable when this
# script is executed directly (e.g., via `uv run python tests/...`).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from x402_xrpl.client import (  # noqa: E402
    XRPLPresignedPaymentPayer,
    XRPLPresignedPaymentPayerOptions,
)
from x402_xrpl.client.presigned_payment_payer import to_currency_hex  # noqa: E402
from x402_xrpl.types import PaymentRequirements  # noqa: E402

XRPL_RPC = os.getenv("XRPL_TESTNET_RPC_URL", "https://s.altnet.rippletest.net:51234/")
XRPL_TESTNET_FAUCET_URL = os.getenv(
    "XRPL_TESTNET_FAUCET_URL",
    "https://faucet.altnet.rippletest.net/accounts",
)
SKIP_FAUCET = os.getenv("XRPL_SKIP_FAUCET", "false").lower() in {"1", "true", "yes"}

RESOURCE_URL = os.getenv("XRPL_RESOURCE_URL", "http://127.0.0.1:8080/xrpl-demo/resource")
IOU_TRUSTLINE_LIMIT = os.getenv("XRPL_IOU_TRUSTLINE_LIMIT", "1000000")
IOU_ISSUER_SEED = os.getenv("XRPL_DEMO_ISSUER_SEED")


def fetch_payment_requirements() -> PaymentRequirements:
    response = requests.get(RESOURCE_URL, timeout=60)
    if response.status_code != 402:
        raise RuntimeError(f"Expected 402 Payment Required, got {response.status_code}: {response.text}")
    body = response.json()

    accepts = body.get("accepts") or []
    if not accepts:
        raise RuntimeError(f"402 body missing accepts: {body}")
    raw_reqs = accepts[0]

    return PaymentRequirements.from_dict(raw_reqs)


def redeem_resource(x_payment_header: str) -> requests.Response:
    headers = {"PAYMENT-SIGNATURE": x_payment_header}
    return requests.get(RESOURCE_URL, headers=headers, timeout=180)


def _issuer_from_requirements(req: PaymentRequirements) -> str | None:
    extra = req.extra
    if not isinstance(extra, dict):
        return None
    issuer = extra.get("issuer")
    if not isinstance(issuer, str) or not issuer:
        return None
    return issuer


def ensure_trustline(
    client: JsonRpcClient,
    *,
    holder: Wallet,
    currency: str,
    issuer: str,
    limit: str,
) -> None:
    tx = TrustSet(
        account=holder.classic_address,
        limit_amount=IssuedCurrencyAmount(currency=to_currency_hex(currency), issuer=issuer, value=str(limit)),
    )
    submit_and_wait(tx, client, holder)


def issue_iou(
    client: JsonRpcClient,
    *,
    issuer_wallet: Wallet,
    destination: str,
    currency: str,
    value: str,
) -> None:
    tx = Payment(
        account=issuer_wallet.classic_address,
        destination=destination,
        amount=IssuedCurrencyAmount(
            currency=to_currency_hex(currency),
            issuer=issuer_wallet.classic_address,
            value=str(value),
        ),
    )
    submit_and_wait(tx, client, issuer_wallet)


def get_iou_balance(
    client: JsonRpcClient,
    *,
    holder: Wallet,
    currency: str,
    issuer: str,
) -> Decimal:
    """
    Return the holder's balance on the trustline (currency, issuer).

    NOTE: In XRPL `account_lines`, the `balance` is from the holder's perspective:
      - positive: holder owns IOUs issued by `issuer`
      - negative: holder owes IOUs to `issuer`
    """
    target_currency = to_currency_hex(currency)
    marker = None

    while True:
        resp = client.request(
            AccountLines(
                account=holder.classic_address,
                peer=issuer,
                marker=marker,
            )
        )
        result = resp.result or {}
        lines = result.get("lines") or []
        for line in lines:
            if not isinstance(line, dict):
                continue
            if line.get("account") != issuer:
                continue
            line_currency = line.get("currency")
            if not isinstance(line_currency, str):
                continue
            if to_currency_hex(line_currency) != target_currency:
                continue
            bal = line.get("balance")
            if not isinstance(bal, str):
                raise RuntimeError("invalid_account_lines_balance")
            try:
                return Decimal(bal)
            except Exception as exc:
                raise RuntimeError(f"invalid_account_lines_balance:{bal}") from exc

        marker = result.get("marker")
        if not marker:
            break

    raise RuntimeError("missing_trustline")


def main() -> None:
    """
    End-to-end script (requires running servers + network access):

      1) Start presigned facilitator:
           uv run python app/services/xrpl_x402_presigned_payment_facilitator.py
      2) Start demo server:
           uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
      3) Run this script:
           uv run python tests/test_script_xrpl_presigned_flow.py
    """

    sender = Wallet.from_seed(os.getenv("XRPL_DEMO_SENDER_SEED", "sEd7M69Yu4Kz8JkunvshAzrPwwdQYQL"))
    receiver = Wallet.from_seed(os.getenv("XRPL_DEMO_RECEIVER_SEED", "sEd73youjTvFdc6koXuxMac5ppmse6e"))

    print(f"Sender: {sender.classic_address}")
    print(f"Receiver: {receiver.classic_address}")

    payment_requirements = fetch_payment_requirements()
    print("\nReceived payment requirements:")
    print(json.dumps(payment_requirements.to_dict(), indent=2))

    issuer_address: str | None = None
    issuer_wallet: Wallet | None = None
    if payment_requirements.asset.upper() != "XRP":
        issuer_address = _issuer_from_requirements(payment_requirements)
        if not issuer_address:
            raise RuntimeError('IOU paymentRequirements missing extra["issuer"]')
        if IOU_ISSUER_SEED:
            issuer_wallet = Wallet.from_seed(IOU_ISSUER_SEED)
            if issuer_wallet.classic_address != issuer_address:
                raise RuntimeError(
                    "XRPL_DEMO_ISSUER_SEED classic address does not match paymentRequirements.extra.issuer"
                )
            print(f"Issuer: {issuer_wallet.classic_address}")
        else:
            print(
                "\nIOU demo: XRPL_DEMO_ISSUER_SEED not set; skipping IOU issuance. "
                "Ensure the sender already holds the IOU balance and both sender/receiver "
                "have trustlines to the issuer."
            )

    if not SKIP_FAUCET:
        wallets_to_fund = [sender, receiver]
        if issuer_wallet is not None:
            wallets_to_fund.append(issuer_wallet)

        for wallet in wallets_to_fund:
            print(f"Funding {wallet.classic_address}...")
            resp = requests.post(
                XRPL_TESTNET_FAUCET_URL,
                json={"destination": wallet.classic_address},
                timeout=300,
            )
            print(f"  Faucet response: {resp.status_code}")

        print("Waiting for ledger to confirm funding...")
        time.sleep(10)

    xrpl_client = JsonRpcClient(XRPL_RPC)

    if payment_requirements.asset.upper() != "XRP":
        assert issuer_address is not None

        print("\nSetting trustlines for IOU asset...")
        ensure_trustline(
            xrpl_client,
            holder=sender,
            currency=payment_requirements.asset,
            issuer=issuer_address,
            limit=IOU_TRUSTLINE_LIMIT,
        )
        ensure_trustline(
            xrpl_client,
            holder=receiver,
            currency=payment_requirements.asset,
            issuer=issuer_address,
            limit=IOU_TRUSTLINE_LIMIT,
        )

        print("\nChecking IOU balance on sender...")
        sender_iou_balance = get_iou_balance(
            xrpl_client,
            holder=sender,
            currency=payment_requirements.asset,
            issuer=issuer_address,
        )
        required_iou_amount = Decimal(str(payment_requirements.amount))

        if sender_iou_balance < required_iou_amount:
            if issuer_wallet is None:
                raise RuntimeError(
                    f"insufficient_iou_balance: have={sender_iou_balance} need={required_iou_amount}. "
                    "Pre-fund the sender with IOUs or set XRPL_DEMO_ISSUER_SEED so the script can mint."
                )

            to_issue = required_iou_amount - sender_iou_balance
            print(f"\nIssuing IOUs to payer (top-up): {to_issue}...")
            issue_iou(
                xrpl_client,
                issuer_wallet=issuer_wallet,
                destination=sender.classic_address,
                currency=payment_requirements.asset,
                value=str(to_issue),
            )
        else:
            print(f"\n✓ Sender has sufficient IOU balance: {sender_iou_balance} >= {required_iou_amount}")

    payer = XRPLPresignedPaymentPayer(
        XRPLPresignedPaymentPayerOptions(
            wallet=sender,
            network=payment_requirements.network,  # type: ignore[arg-type]
            rpc_url=XRPL_RPC,
        )
    )

    print("\nBuilding presigned Payment tx and PAYMENT-SIGNATURE header...")
    x_payment_header = payer.create_payment_header(payment_requirements)

    print("\nCalling resource server with PAYMENT-SIGNATURE header...")
    response = redeem_resource(x_payment_header)
    print(f"Resource response: {response.status_code}")
    print(f"Response body: {response.text}")

    if response.status_code != 200:
        raise RuntimeError("Resource access failed")

    if "PAYMENT-RESPONSE" in response.headers:
        decoded = json.loads(base64.b64decode(response.headers["PAYMENT-RESPONSE"]))
        print("\n✓ Settlement complete!")
        print(json.dumps(decoded, indent=2))


if __name__ == "__main__":
    main()
