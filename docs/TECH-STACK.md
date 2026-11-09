# Technical Stack

## Recommended stack (hackathon-sized, testable)

| Layer | Choice | Responsibility |
|---|---|---|
| Frontend | Next.js + TypeScript | Dashboard, upload, charts, reviewer workflows |
| UI | Tailwind CSS + shadcn/ui (or equivalent) | Consistent accessible components |
| Charts | Recharts | Temperature timeline and analytics |
| Backend | Python FastAPI | CSV processing, rules engine, workflow API |
| Validation | Pydantic | Typed request/response contracts |
| Data | PostgreSQL in deployment; SQLite for local quick-start only if migrations support both | Shipments, events, decisions, payment records |
| ORM/migrations | SQLAlchemy + Alembic | Persistence and schema evolution |
| File storage | Local dev storage; S3-compatible object storage in deployment | Original evidence and report files |
| AI | Optional Gemini API | Extract structured fields from supporting documents and explain findings |
| Payments | PayPal Orders v2 REST API | Sandbox order, authorisation, capture, void |
| Tests | pytest + HTTPX; Vitest/Playwright for frontend/E2E | Unit, API, UI and workflow testing |
| Deployment | Vercel frontend + Render/Fly.io backend + managed PostgreSQL/object storage | Public demo |

## Keep the system small
Use one frontend and one backend service. Do not add microservices, Kafka, vector databases, blockchain, or live IoT integrations for the MVP.

## AI boundary
AI may:
- Extract product name, storage range, document date, logger metadata, and source text into a structured draft.
- Summarise deterministic findings in plain English.
- Suggest which missing evidence a reviewer should request.

AI may not:
- Invent product limits.
- Certify medicine viability or regulatory compliance.
- Change deterministic analysis results.
- Approve/reject shipments.
- Capture/void payments.

Every extracted value must retain source text/page/field and require confirmation before becoming an active product profile.

## Environment variables (names only)
Frontend:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_PAYPAL_CLIENT_ID` (only if the chosen PayPal frontend SDK flow requires it)

Backend:
- `DATABASE_URL`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`
- `PAYPAL_BASE_URL` (sandbox URL in development)
- `GEMINI_API_KEY` (optional)
- `APP_SECRET_KEY`
- `FILE_STORAGE_PATH` or object-storage credentials
- `CORS_ORIGINS`

Never expose `PAYPAL_CLIENT_SECRET`, Gemini keys, database credentials, or signing secrets to the browser. Include `.env.example` with placeholders only.
