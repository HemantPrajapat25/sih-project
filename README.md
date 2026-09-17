# NumberGuard 🛡️
### Privacy-Preserving B2B Telecom Infrastructure for Mobile Number Lifecycle & Reallocation Risk Management

---

## 📌 Problem Statement

Telecom operators permanently disconnect millions of mobile numbers every year and later reallocate them to new subscribers. However, previously used numbers frequently remain associated with bank accounts, UPI apps, payment gateways, e-commerce profiles, and digital identity recovery channels.

If a recycled number is assigned to a new customer before the digital ecosystem has detached old associations, the new subscriber receives unexpected OTPs, debt recovery calls, or faces privacy and identity collisions.

**NumberGuard** provides telecom operators with an automated, privacy-preserving infrastructure to:
1. Orchestrate statutory cooling and quarantine periods before number reallocation.
2. Dispatch pseudonymized challenge unlinking notifications to registered digital service providers (banks, fintechs, e-commerce, identity platforms).
3. Compute deterministic residual reassignment risk scores (0–100).
4. Provide audit-grade allocation readiness recommendations certifying when a number is safe to release.

---

## 🔒 Privacy-By-Design Guarantees

NumberGuard **strictly forbids**:
- Storing or exposing previous owner identities, names, or addresses.
- Scraping external websites or harvesting private user records.
- Storing subscriber passwords, credentials, or private message contents.

All phone numbers are indexed with **HMAC-SHA256 hashes** with private server-side pepper keys, displayed masked (`+91 98**** *210`), and dispatched to external providers using opaque challenge tokens (`REF-A3E89B1F20C1`).

---

## 🏗️ Architecture & Monorepo Structure

```
/sih-2026
├── /frontend               # Next.js 16 (App Router), TypeScript, Tailwind CSS, Recharts
│   ├── app/                # 14 enterprise telecom pages (Dashboard, Numbers, Queue, Risk, etc.)
│   ├── components/         # Metric cards, Timeline, Status chips, Risk gauges, Import modal
│   ├── lib/                # Typed API client, Auth Context, RBAC permissions
│   └── types/              # Comprehensive TypeScript interfaces
├── /backend                # Python FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic
│   ├── app/
│   │   ├── api/v1/         # Modular REST routers (auth, numbers, risk, providers, audit, etc.)
│   │   ├── core/           # RBAC matrix, privacy hashing & masking, JWT security, config
│   │   ├── db/             # Dynamic SQLite / PostgreSQL async session handler
│   │   ├── models/         # SQLAlchemy 2.0 models (Number, Provider, Notification, Cooling, Audit)
│   │   ├── schemas/        # Pydantic validation schemas with ConfigDict
│   │   ├── services/       # Risk engine, lifecycle orchestrator, audit logger, notification dispatcher
│   │   └── adapters/       # Clean sandbox/mock adapters for carrier feeds & banking webhooks
│   └── tests/              # Pytest unit & integration test suite (8/8 passing)
├── /worker                 # Background task runner evaluating cooling expiries & SLA overdue timers
├── /database               # Alembic migrations & initial data seeder (`seed.py`)
├── /infra                  # Production Dockerfiles (Backend, Frontend, Worker)
├── /docs                   # Architecture spec, Privacy-By-Design blueprint
├── /scripts                # Setup, development runner, test runner, and data seeder scripts
├── docker-compose.yml      # Multi-container orchestration (Postgres 16, Redis 7, Backend, Frontend, Worker)
└── .env.example            # Centralized environment variable template
```

---

## 👥 Granular RBAC Personas

NumberGuard provides strict Role-Based Access Control enforced at the backend API layer:

| Role | Organization Type | Primary Privilege Scope |
|---|---|---|
| `SUPER_ADMIN` | Regulatory Authority | Global platform administration, tenant provisioning |
| `TELECOM_ADMIN` | Operator (Jio, Airtel, Vi) | Organization numbers, cooling rule policies, risk overrides, release approvals |
| `TELECOM_OPERATOR` | Operator Ops Engineer | Batch number decommissioning, status reviews |
| `SERVICE_PROVIDER_ADMIN` | Bank / Fintech Lead (HDFC, Paytm) | Webhook configuration, SLA parameters |
| `SERVICE_PROVIDER_OPERATOR` | Provider SecOps | Unlinking alert acknowledgment & remediation |
| `AUDITOR` | Compliance Agency (Deloitte) | Read-only tamper-evident audit inspection |
| `ANALYST` | Telecom Analytics Bureau | Read-only aggregate risk distributions & trends |

> 💡 **Developer Sandbox**: The login page and top navigation bar include a **1-click Role Switcher** to instantly test and preview the platform under any of the 7 RBAC roles without entering credentials.

---

## 🚀 Quickstart Guide

### Option 1: Native Local Run (Zero External Dependencies)

1. **Setup Dependencies**:
   ```bash
   ./scripts/setup.sh
   ```

2. **Run Tests**:
   ```bash
   ./scripts/run_tests.sh
   ```

3. **Start Development Servers**:
   ```bash
   ./scripts/run_dev.sh
   ```
   - **Frontend Dashboard**: `http://localhost:3000`
   - **FastAPI Backend & Swagger Docs**: `http://localhost:8000/docs`

### Option 2: Docker Compose (PostgreSQL 16 + Redis + Worker + Web)

```bash
docker compose up --build
```

---

## 📊 Core Pages & Features

1. **Dashboard** (`/`): Real-time metrics (numbers managed, in cooling, high-risk holds, ready for release), lifecycle velocity bar chart, risk distribution donut, recent compliance activity.
2. **Numbers Inventory** (`/numbers`): Directory with masked numbers, carrier filters, status pills, risk scores, and CSV import modal.
3. **Number Detail** (`/numbers/[id]`): Lifecycle progression timeline, risk factor breakdown, provider unlinking status, and manual override dialog.
4. **Decommissioning Queue** (`/queue`): Operational queue triaging cooling expirations, high-risk holds, and pending partner responses.
5. **Risk Engine** (`/risk`): Algorithmic weighting model breakdown with interactive real-time risk simulator.
6. **Service Providers** (`/providers`): Directory of 8 registered partners (HDFC, SBI, Paytm, PhonePe, Amazon, Flipkart, WhatsApp, Google) with SLA stats and test ping sandbox.
7. **Notifications Hub** (`/notifications`): Log of dispatched unlinking events with opaque challenge references and remediation ack action.
8. **Cooling Periods** (`/cooling`): Policy editor for minimum quarantine days (Standard 60d, Banking 90d, High Risk 120d).
9. **Allocation Readiness** (`/readiness`): Decision clearance matrix with blocked reasons hierarchy and batch carrier release approval tool.
10. **Audit Trail** (`/audit`): Searchable, immutable compliance logs with correlation ID inspector and state diff modal.
11. **Analytics** (`/analytics`): Intake vs release volume velocity and partner response SLA performance.
12. **API & Integrations** (`/integrations`): Carrier feed adapters (Jio, Airtel, Vi) and external webhook tester.
13. **Users & Roles** (`/users`): RBAC matrix inspector across all 13 granular permissions.
14. **Organization Settings** (`/settings`): Carrier tenant configuration and retention parameters.
15. **Authentication Portal** (`/login`): Secure sign-in with 1-click dev role switching.
