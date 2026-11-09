# coldchain-sentinel
Evidence-driven pharmaceutical cold-chain verification and PayPal-powered payment assurance platform.

**Tagline:** Every Degree Matters. Every Payment Must Be Earned.

ColdChain Sentinel connects pharmaceutical shipment requirements, continuous temperature logger telemetry, evidence-integrity checks, chain-of-custody handovers, authorized human quality review, and PayPal payment actions into an auditable workflow.

> [!IMPORTANT]
> **Scope & Safety Boundary:** ColdChain Sentinel verifies temperature telemetry and evidence integrity against configured product-specific criteria. Temperature compliance does **not** independently prove that medicine is biologically safe or viable. Final product disposition remains with an authorized human quality reviewer. AI is strictly non-authoritative and can never approve shipments or trigger payments. PayPal authorization is conditional payment flow, not escrow.

---

## 1. System Architecture

```
                                    +-----------------------------+
                                    |     Next.js Web Console     |
                                    |  (Pure Charcoal / No Blue)  |
                                    +--------------+--------------+
                                                   |
                                                   v
                                    +-----------------------------+
                                    |     FastAPI Python Core     |
                                    +--------------+--------------+
                                                   |
                   +-------------------------------+-------------------------------+
                   |                               |                               |
                   v                               v                               v
    +------------------------------+ +---------------------------+ +-------------------------------+
    |  Deterministic Rules Engine  | |   Evidence Trust Engine   | |    Payment State Guard        |
    |  • Product min/max bounds    | |   • Instant SHA-256 hash  | |    • 5-Factor Capture Guard   |
    |  • Excursion duration        | |   • Monotonic timestamps  | |    • Idempotency key table    |
    |  • Sampling intervals & gaps | |   • Hardware ID matching  | |    • PayPal Sandbox / Demo    |
    +------------------------------+ +---------------------------+ +-------------------------------+
```

---

## 2. Five-Factor Payment Safety Guardrails

Payment capture eligibility strictly requires:
1. **Product-Specific Rule Compliance:** Telemetry falls strictly within configured temperature bounds with zero critical excursions.
2. **Complete Evidence Validation:** Valid SHA-256 checksum, no duplicate or out-of-order timestamps, verified sampling continuity, and matching logger ID.
3. **Authorized Human Review:** An authenticated user with the `REVIEWER` role explicitly approves the delivery with an audit reason.
4. **Valid PayPal Authorization State:** Active PayPal order in `AUTHORIZED` status within the valid capture window.
5. **Idempotency Protection:** Unique, database-enforced idempotency key (`IDEMP-<shipment>-<action>-<hash>`) prevents duplicate settlement.

---

## 3. Technology Stack

- **Backend Runtime:** Python 3.13.2 (Pinned deployment target: `python:3.12-slim` / `python:3.13-slim`)
- **API Framework:** FastAPI 0.162.2 + Pydantic v2 (Pydantic 2.14.3)
- **Database:** SQLAlchemy 2.1.8 + Alembic 1.20.1 (SQLite local development; PostgreSQL deployment ready with `render_as_batch=True`)
- **Frontend:** Next.js 14 + React 18 + TypeScript + Tailwind CSS (Charcoal Ops Palette: `#090a0c`, `#121316`, `#1a1b1f`, `#282a2e`, `#f4f4f5`, `#8c8e96`)
- **Maps:** Leaflet + Natural Cartography (Natural land/ocean tones; zero neon/blue overlays; discrete handover waypoints only)
- **Payments:** PayPal Orders v2 REST API (Sandbox) + Deterministic Demo Mode
- **Reports:** Server-side audit PDF generation via ReportLab 5.1.0

---

## 4. Development Roadmap (12 Phases)

1. **PHASE 1** — Project architecture, directory structure and repository setup *(Complete)*
2. **PHASE 2** — Backend and database schema (SQLAlchemy + Alembic batch migrations)
3. **PHASE 3** — Authentication and user roles (`BUYER`, `COURIER`, `REVIEWER`, `ADMIN`)
4. **PHASE 4** — Shipment management & product storage requirements
5. **PHASE 5** — Deterministic temperature intelligence & excursion engine
6. **PHASE 6** — Evidence Trust Engine (multi-factor integrity & hardware matching)
7. **PHASE 7** — Chain-of-custody tracking & handover timeline
8. **PHASE 8** — PayPal Orders v2 Sandbox integration & Demo mode
9. **PHASE 9** — Investigations, reviewer decisions & ReportLab PDF generation
10. **PHASE 10** — Carrier intelligence & reliability metrics
11. **PHASE 11** — Sentinel Challenge evaluation testbed
12. **PHASE 12** — Frontend integration, end-to-end verification, deployment & audit

---

## 5. Verification & Testing

To run the automated test suite from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -c backend/pytest.ini
```

---

## 6. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
