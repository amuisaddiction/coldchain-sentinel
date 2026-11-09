# API and PayPal Flow

## Application API (proposed)

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/shipments` | Create shipment |
| GET | `/api/shipments` | List/filter shipments |
| GET | `/api/shipments/{id}` | Shipment detail |
| POST | `/api/shipments/{id}/evidence` | Upload CSV/supporting files |
| POST | `/api/shipments/{id}/analyze` | Run deterministic analysis |
| GET | `/api/shipments/{id}/analysis/latest` | Fetch findings |
| POST | `/api/shipments/{id}/custody-events` | Add handover |
| POST | `/api/shipments/{id}/review` | Approve/reject/request evidence |
| POST | `/api/shipments/{id}/payment/create-order` | Create PayPal order |
| POST | `/api/shipments/{id}/payment/authorize` | Authorise approved buyer order |
| POST | `/api/shipments/{id}/payment/capture` | Capture after guard checks |
| POST | `/api/shipments/{id}/payment/void` | Void active authorisation |
| POST | `/api/paypal/webhook` | Verify and process PayPal webhook |
| GET | `/api/shipments/{id}/report` | Generate/download report |
| GET | `/api/analytics/carriers` | Carrier metrics |

All routes require authentication/role checks in a production system. For a hackathon demo, if authentication is omitted, disclose that it is a controlled prototype and do not expose real customer or payment data.

## PayPal sequence

1. Backend creates an Orders v2 order using `intent: AUTHORIZE`.
2. Buyer approves the order through PayPal's supported approval flow.
3. Backend authorises the order and stores order/authorisation IDs and returned status.
4. Shipment evidence is uploaded and analysed.
5. Reviewer approves only if mandatory checks pass.
6. Backend checks current shipment state, authorisation status, reviewer decision, and idempotency key.
7. Backend calls capture endpoint and persists the actual response.
8. On rejection, backend requests void for the active authorisation and persists the actual response.
9. Webhook endpoint verifies signature and reconciles state.

## Critical PayPal caveats
- Authorisation is not escrow.
- Authorisations are time-limited; check current PayPal documentation for current validity and capture windows. Do not promise that money is held indefinitely.
- A void request does not guarantee a bank/card issuer immediately removes a pending hold from the buyer's statement.
- Refunds apply to captured payments and are a separate flow; do not confuse refund with void.
- Some API features, permissions, and account eligibility vary. Verify sandbox credentials and permissions before committing to the demo.
- Never claim a transaction succeeded until PayPal returns a successful state or a verified webhook confirms it.

## Demo Mode
- A separate adapter returns deterministic simulated order/authorisation/capture/void IDs prefixed `DEMO-`.
- Every screen and report carries a prominent `SIMULATED — DEMO MODE` label.
- Demo Mode must never call PayPal or be presented as a real payment.
