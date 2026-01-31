# XRPL x402 Facilitator

x402 facilitator for the **XRPL (XRP Ledger)** implementing the `exact` payment scheme using a **payer-signed presigned `Payment` transaction blob**.

## XRPL x402 Flow

![XRPL x402 Flow](assets/diagram-export-12-6-2025-9_37_24-PM.png)

### How It Works

1. **Client** requests a protected resource → Server returns `402 Payment Required` with payment requirements (includes `invoiceId`)
2. **Client** builds an XRPL `Payment` transaction:
   - `Destination = payTo`
   - `Amount = amount` (drops for XRP; `value` string for IOUs)
   - `SourceTag = 804681468` (default; override via `paymentRequirements.extra.sourceTag`)
   - invoice binding via `Memos` + `InvoiceID` (both)
   - `LastLedgerSequence` present
3. **Client** signs the `Payment` and sends `PAYMENT-SIGNATURE` (base64-encoded x402 v2 `PaymentPayload` with `signedTxBlob`)
4. **Server** calls Facilitator `/verify` → Facilitator decodes `tx_blob`, checks invariants + invoice binding
5. **Server** calls Facilitator `/settle` → Facilitator submits `tx_blob` to XRPL (optionally waits for validated)
6. **Server** returns the resource with `PAYMENT-RESPONSE`

## Quickstart

### 1. Install dependencies

```bash
uv sync
```

### 2. Start the Facilitator service

```bash
uv run python app/services/xrpl_x402_presigned_payment_facilitator.py
# Runs on http://127.0.0.1:8011
```

### 3. Start the Demo server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
# Demo resource at http://127.0.0.1:8080/xrpl-demo/resource
```

### 4. Run the test script

```bash
uv run python tests/test_script_xrpl_presigned_flow.py
```

To demo an IOU payment (non-XRP), put these in `.env.local` (or `.env`) **before starting** the demo server:

```bash
# .env.local
XRPL_DEMO_ASSET=RLUSD
XRPL_DEMO_ISSUER=r...
# Optional: only needed if you want `tests/test_script_xrpl_presigned_flow.py`
# to mint test IOUs to the payer (must match XRPL_DEMO_ISSUER).
XRPL_DEMO_ISSUER_SEED=sEd...
XRPL_DEMO_AMOUNT=1
# XRPL_IOU_TRUSTLINE_LIMIT=1000000
```

### 5. Run the browser demo (optional)

The repository includes a Next.js browser demo under `demo-frontend/web` that signs an XRPL `Payment` transaction in the browser and sends it as `PAYMENT-SIGNATURE`.

For full instructions, see `demo-frontend/web/README.md`. Quick version:

```bash
# Terminal A (backend)
uv run python app/services/xrpl_x402_presigned_payment_facilitator.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080

# Terminal B (frontend)
cd demo-frontend/web
cp env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 and click **Run Demo**.

## API Endpoints

### Facilitator (`localhost:8011`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/supported` | GET | Supported scheme/network pairs |
| `/verify` | POST | Verify `PAYMENT-SIGNATURE` header + `Payment` tx invariants (no broadcast) |
| `/settle` | POST | Submit the payer-signed `Payment` tx blob to XRPL |

### Demo Server (`localhost:8080`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/xrpl-demo/resource` | GET | x402-protected resource (returns 402 without payment) |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `XRPL_FACILITATOR_HOST` | `127.0.0.1` | Facilitator bind host |
| `XRPL_FACILITATOR_PORT` | `8011` | Facilitator bind port |
| `XRPL_FACILITATOR_BASE_URL` | `http://127.0.0.1:8011` | Facilitator URL for demo server |
| `XRPL_DEMO_PAYTO` | (testnet address) | Payee address for demo |
| `XRPL_DEMO_AMOUNT_DROPS` | `1000000` | Payment amount in drops (1 XRP) |
| `XRPL_DEMO_ASSET` | `XRP` | Payment asset (`XRP` or an IOU code like `RLUSD`) |
| `XRPL_DEMO_ISSUER` | (none) | IOU issuer (required when `XRPL_DEMO_ASSET != XRP`) |
| `XRPL_DEMO_AMOUNT` | (none) | IOU amount string (e.g. `1`, `1.25`) |

## Key Features

- **Presigned `Payment` settlement**: Facilitator submits a payer-signed `Payment` tx blob
- **Invoice binding enforcement**: Requires invoice id to be embedded in the signed transaction
- **Multi-asset support**: Native XRP and direct IOU payments (via `asset` + `extra.issuer`)
- **Safety checks**: Fee cap + rejects unsupported Payment features (e.g. `Paths`, `SendMax`, partial payments)
- **Validated settlement (recommended)**: Can wait for `validated=true` before returning success

## Network

Currently configured for **XRPL Testnet** (`s.altnet.rippletest.net`).

To get testnet XRP, use the [XRPL Testnet Faucet](https://faucet.altnet.rippletest.net/).

## License

MIT
