# AI API Security Agent

[![CI](https://github.com/Deepali123verma/AI-API-Security-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Deepali123verma/AI-API-Security-Agent/actions/workflows/ci.yml)

**AI-powered API security auditing platform that combines deterministic security scanning, risk scoring, and Gemini-based reasoning to identify and explain potential REST API security risks.**

Upload an OpenAPI/Swagger specification → discover endpoints → run deterministic scanners → score risk → optionally request Gemini analysis → download PDF reports → compare scans for security regression.

> Gemini never replaces scanners and never overrides `risk_score` or severity. Deterministic evidence remains authoritative.

---

## The problem

Modern REST APIs are documented in OpenAPI, but documentation alone does not answer:

- Which endpoints lack authentication?
- Where could authorization or injection risks appear in the contract?
- What is the overall risk posture, and did it improve or worsen after a change?

Manual review does not scale. Blindly trusting an LLM to “find vulnerabilities” can invent issues and hide provenance.

**AI API Security Agent** keeps scanning deterministic and explainable, then uses Gemini only as an optional reasoning layer for summaries, prioritization, and remediation guidance.

---

## How the workflow works

```text
Upload OpenAPI (JSON/YAML)
        ↓
Parse & store endpoints
        ↓
Run deterministic security scanners
        ↓
Generate findings + evidence + risk scores
        ↓
(Optional) Gemini analysis per finding
        ↓
Review in React dashboard / download PDF report
        ↓
Compare against a baseline scan (regression)
```

Architecture:

```text
                    ┌─────────────────────┐
                    │   React Dashboard   │
                    └──────────┬──────────┘
                               │ JWT + REST
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
     OpenAPI Parser    Security Scanners    Gemini Agent
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                        Risk Scoring
                               │
                               ▼
                         PostgreSQL
                               │
             ┌─────────────────┴─────────────────┐
             ▼                                   ▼
      PDF Security Reports              Regression Analysis
```

---

## Main security checks

Deterministic scanners inspect the uploaded OpenAPI contract (static analysis — **not** active penetration testing):

| Scanner | Focus |
|---------|--------|
| Authentication | Missing or weak auth requirements on operations |
| Authorization | Object identifiers / access-control related signals in the spec |
| Sensitive data | Sensitive field names in requests/responses |
| Rate limiting | Missing or incomplete rate-limit related documentation signals |
| Configuration | Security-relevant configuration gaps in the spec |
| Injection | Injection-prone parameter patterns in the contract |

Findings include title, category, severity, evidence, confidence, remediation hints, and structured risk factors.

---

## Deterministic scanner + Gemini reasoning

| Layer | Role |
|-------|------|
| **Deterministic scanners** | Produce findings and evidence from the OpenAPI spec |
| **Risk scoring** | Assign explainable `risk_score` (0–100) and `risk_level` |
| **Gemini (optional)** | Summarize why it matters, technical reasoning, validation guidance, remediation, priority, limitations |

Rules enforced in the product:

- AI is **not** auto-run when you execute a security scan
- AI is requested per finding from the dashboard/API
- AI does **not** invent endpoints or override scores
- `GEMINI_API_KEY` stays on the backend only — never in the browser

---

## Risk scoring

Scoring is fully deterministic. The same finding and endpoint context always produces the same `risk_score`, `risk_level`, and `risk_factors`.

| Severity | Base Score |
|----------|------------|
| CRITICAL | 90 |
| HIGH | 75 |
| MEDIUM | 50 |
| LOW | 25 |
| INFO | 10 |

Scores are clamped to `0–100`. Adjustments use documented risk factors (for example sensitive data or authentication context). Gemini never overrides these values.

---

## Scan history

- Paginated scan list with optional `status` and `risk_level` filters
- Status lifecycle includes values such as `PENDING`, `PARSING`, `COMPLETED`, `FAILED`
- Scan detail with endpoint/finding summaries and AI analysis counts
- Safe delete for scans you own

---

## AI analysis

1. Open a finding detail page
2. Click **Analyze with Gemini** → `POST /api/v1/scans/{scan_id}/findings/{finding_id}/analyze`
3. Use **Refresh analysis** for `force_refresh=true`
4. If Gemini is unavailable (`503`), the deterministic finding remains visible

Stored AI fields include summary, why it matters, technical reasoning, validation guidance, remediation, priority, and limitations.

---

## Security regression / comparison

Compare a current scan against a baseline scan owned by the same user.

- API: `GET /api/v1/scans/{scan_id}/compare/{baseline_scan_id}`
- Optional PDF: `GET /api/v1/scans/{scan_id}/compare/{baseline_scan_id}/report/pdf`
- Dashboard: `/scans/:scanId/compare` and `/regression` hub

Finding fingerprints (deterministic, no DB IDs, no AI fields):

```text
normalized(category) | normalized(title) | HTTP method | path
```

Classification:

- **NEW** — present in current, not baseline
- **RESOLVED** — present in baseline, not current
- **PERSISTENT** — present in both

Posture:

```text
risk_score_change = current_score - baseline_score
```

- negative → `IMPROVED`
- positive → `WORSENED`
- zero → `UNCHANGED`

---

## Reports

PDF security assessment reports are generated on the backend with ReportLab.

- `GET /api/v1/scans/{scan_id}/report/pdf`
- JWT + ownership enforced
- Includes metadata, executive summary, severity distribution, and findings
- Gemini content appears only when already stored under AI-assisted analysis
- Frontend: **Download security report** on the scan detail page

Reports never invent findings and never recalculate Phase 5 risk scores.

---

## Frontend dashboard

React + TypeScript + Vite dashboard with a security-oriented UI:

- Login / register (JWT in `localStorage` for this portfolio demo)
- Protected routes and sign-out
- Dashboard: live metrics, overall security posture gauge, findings-by-severity, recent scans, latest findings, AI analysis card
- Scans: upload OpenAPI, search/filters, pagination, delete
- Scan detail: run security scan, risk posture, expandable findings
- Endpoints inventory and findings explorer (nested routes + top-level hubs)
- Regression / compare workspace
- Finding detail with clear **Deterministic Scanner Result** vs **AI Reasoning** sections

Routes include `/login`, `/register`, `/dashboard`, `/scans`, `/scans/:scanId`, `/endpoints`, `/findings`, `/regression`, and nested findings/compare paths.

---

## Tech stack

**Backend**

- Python 3.12+, FastAPI, Uvicorn, Pydantic v2
- SQLAlchemy 2.x, PostgreSQL, psycopg, Alembic
- pwdlib (Argon2), PyJWT
- openapi-spec-validator, PyYAML
- google-genai (optional Gemini)
- reportlab (PDF reports)
- pytest

**Frontend**

- Vite, React, TypeScript
- React Router, Axios, Tailwind CSS, Lucide React
- Vitest + Testing Library

**Ops**

- Vercel (`vercel.json` + FastAPI function + `public/` SPA)
- Docker Compose / root `Dockerfile` (optional container path)
- GitHub Actions CI

---

## Project structure

```text
ai-api-security-agent/
├── .github/workflows/ci.yml
├── vercel.json                # Vercel: FastAPI + SPA same domain
├── main.py                    # Vercel FastAPI entrypoint
├── requirements.txt           # Vercel Python deps
├── pyproject.toml             # Vercel entrypoint hint
├── Dockerfile                 # Optional container image
├── railway.toml               # Optional container host hints
├── docker-compose.yml
├── scripts/migrate_db.py      # One-time managed Postgres migrations
├── backend/
│   ├── app/
│   │   ├── agents/          # Gemini reasoning (optional)
│   │   ├── api/routes/      # Auth, scans, findings, compare, reports
│   │   ├── core/            # Config, security, DB
│   │   ├── models/          # SQLAlchemy models
│   │   ├── reports/         # PDF generation
│   │   ├── scanner/         # Deterministic scanners
│   │   ├── scoring/         # Risk scoring engine
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Application services
│   ├── alembic/             # Migrations
│   ├── scripts/start.sh     # Container migrate + uvicorn entrypoint
│   ├── tests/
│   ├── Dockerfile           # API-only image (local/dev)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── context/
│   │   └── layouts/
│   ├── package.json
│   └── .env.example
├── .env.example
└── README.md
```

---

## How to run the backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

Copy environment defaults from the repo root:

```bash
# Windows
copy ..\.env.example ..\.env

# macOS/Linux
# cp ../.env.example ../.env
```

Set a strong `JWT_SECRET_KEY` in the root `.env`. Settings load that file when you run uvicorn from `backend/`.

Ensure the `security_agent` database exists in PostgreSQL, then:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Or with Docker from the project root (API + Postgres):

```bash
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

Optional local **full-stack** image (FastAPI serves the built React SPA on one port):

```bash
docker compose --profile fullstack up --build web db
```

- App: http://localhost:8080

For local uvicorn (not Docker), `DATABASE_URL` must use `localhost` and credentials that match your PostgreSQL install. Compose uses host `db` with user/password/db `postgres` / `postgres` / `security_agent`.

---

## How to run the frontend

```bash
cd frontend
copy .env.example .env   # or: cp .env.example .env
npm install
npm run dev
```

Dashboard: http://localhost:5173

### Running both locally

1. Start PostgreSQL and the FastAPI backend
2. Confirm `CORS_ORIGINS` includes `http://localhost:5173`
3. Start the React app with `npm run dev`
4. Register → sign in → upload OpenAPI → run security scan → optionally analyze findings / compare scans

---

## Production deployment (Vercel)

### Recommended platform: Vercel

This repository is configured for **one Vercel project** with:

- React/Vite SPA on the CDN (`public/` build output)
- FastAPI as a Vercel Function (`main.py` → `backend/app/main.py`)
- **Same public domain** for UI + API (`/auth`, `/api/v1`, `/health`, `/docs`)
- Managed **PostgreSQL** from an external provider (Neon recommended; Vercel Postgres is also fine)

| Need | How this Vercel setup fits |
|------|----------------------------|
| One public URL | SPA + API rewrites on the same `*.vercel.app` domain |
| FastAPI | Official Python/FastAPI runtime via root `main.py` |
| React/Vite | Built during `buildCommand` into `public/` |
| PostgreSQL | Neon / Vercel Postgres / any Postgres URL via `DATABASE_URL` |
| Gemini | Server-side only (`GEMINI_API_KEY` in Vercel env) |
| GitHub | Import repo and deploy on push |

**Why not split hosts:** Frontend calls use an empty production `VITE_API_BASE_URL`, so the browser talks to the same origin (`/api/v1/...`, `/auth/...`).

**Postgres note:** Vercel does not run Postgres inside the Node/Python function. Use a managed database (this guide assumes **Neon**).

Optional: the root `Dockerfile` / Railway-oriented files remain for container deploys, but **Vercel is the primary path** for this request.

### Deployment architecture

```text
Browser  →  https://<project>.vercel.app
                 │
     ┌───────────┴────────────┐
     ▼                        ▼
 CDN static SPA            FastAPI Function
 (public/index.html,       (main.py → app.main:app)
  /assets/*)                 /health /auth /api/v1
                             /docs /openapi.json
                             Gemini (server-only)
                                   │
                                   ▼
                         Managed PostgreSQL (Neon)
```

### Deploy steps (manual actions — stop here for secrets/login)

1. **Create a Neon (or Vercel Postgres) database**  
   - Neon: https://neon.tech → create project → copy the connection string  
   - Prefer the pooled connection string for serverless if Neon offers one  

2. **Run migrations once** against that database (from your machine, with env vars set locally — do not paste secrets into chat):

```bash
cd backend
# Set DATABASE_URL and JWT_SECRET_KEY in your shell or a local .env (gitignored)
python ../scripts/migrate_db.py
```

3. **Import the GitHub repo on Vercel**  
   - https://vercel.com → Add New Project → `Deepali123verma/AI-API-Security-Agent`  
   - Framework should follow `vercel.json` (`fastapi`)  
   - Root directory: repository root (not `frontend/` alone)

4. **Set Environment Variables** in the Vercel project (Production + Preview as needed):

| Variable | Where | Notes |
|----------|--------|--------|
| `DATABASE_URL` | Vercel (server) | Neon/Postgres URL (app normalizes to `postgresql+psycopg://`) |
| `JWT_SECRET_KEY` | Vercel (server) | Long random secret |
| `CORS_ORIGINS` | Vercel (server) | Your public origin, e.g. `https://<project>.vercel.app` (add custom domain later if used) |
| `GEMINI_API_KEY` | Vercel (server) | Optional |
| `GEMINI_MODEL` | Vercel (server) | Optional (`gemini-2.5-flash`) |
| `JWT_ALGORITHM` | Optional | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Default `30` |

Do **not** set `GEMINI_API_KEY` / `JWT_SECRET_KEY` / `DATABASE_URL` as `VITE_*` variables.

5. **Deploy** and open the Vercel URL. Register a user, upload a small OpenAPI file, run a scan.

### Limits to be aware of

- Serverless **maxDuration** is set to **60s** in `vercel.json` (Pro plan may be required for 60s; Hobby defaults can be lower — adjust in the Vercel dashboard if needed).
- Request body size limits on Vercel may be lower than the app’s 5 MB upload setting; use smaller OpenAPI files on the free tier if uploads fail.
- Cold starts can add latency on the first request after idle.

### Key config files

- `vercel.json` — install/build, function limits, SPA fallback rewrites  
- `main.py` — Vercel FastAPI entrypoint importing `backend`  
- `requirements.txt` — production Python deps for Vercel  
- `pyproject.toml` — `[tool.vercel]` entrypoint hint  
- `scripts/migrate_db.py` — one-time DB bootstrap + Alembic  

### Optional container alternative

```bash
docker compose --profile fullstack up --build web db
```

See older Railway/Docker notes in git history if you prefer a long-running container instead of serverless.

---

## Environment variables

Root `.env` (from `.env.example`):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL |
| `JWT_SECRET_KEY` | Signing key for access tokens |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `GEMINI_API_KEY` | Optional; leave empty to disable live AI calls |
| `GEMINI_MODEL` | Default `gemini-2.5-flash` |
| `GEMINI_TEMPERATURE` | Model temperature |
| `GEMINI_MAX_BULK_FINDINGS` | Bulk analysis guardrail |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `STATIC_DIR` | Optional (Docker image only). Leave unset on Vercel — SPA is in `public/` |

Frontend `.env` (from `frontend/.env.example`):

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Dev: `http://localhost:8000`. Vercel/Docker production build: leave empty for same-origin API calls |

**Never commit real `.env` files, API keys, JWT secrets, or database passwords.**

---

## Testing

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

Backend API tests use an in-memory SQLite setup from `backend/tests/conftest.py` (no production database required). Gemini interactions are mocked in tests.

---

## GitHub Actions / CI

Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

On pushes and pull requests to `main`, CI runs:

1. Backend pytest
2. Alembic migration validation (PostgreSQL service)
3. Frontend Vitest
4. Frontend production build
5. Dependency audit (`npm` high+; `pip-audit` report-only)

Notes:

- `GEMINI_API_KEY` is empty in CI; live Gemini is not called
- No production secrets or cloud deployments are configured in this workflow

---

## Authentication

- `POST /auth/register` — username, email, password
- `POST /auth/login` — OAuth2 form fields `username` + `password` (not email)
- `GET /auth/me` — current user

Frontend route protection is UX only; backend ownership checks remain authoritative. On `401`, the dashboard clears the session and redirects to `/login`.

---

## Selected API endpoints

- `GET /api/v1/scans` — paginated history
- `POST /api/v1/scans` — upload OpenAPI
- `GET /api/v1/scans/{scan_id}`
- `GET /api/v1/scans/{scan_id}/endpoints`
- `GET /api/v1/scans/{scan_id}/findings`
- `POST /api/v1/scans/{scan_id}/security-scan`
- `POST /api/v1/scans/{scan_id}/findings/{finding_id}/analyze`
- `GET /api/v1/scans/{scan_id}/report/pdf`
- `GET /api/v1/scans/{scan_id}/compare/{baseline_scan_id}`
- `GET /api/v1/scans/{scan_id}/compare/{baseline_scan_id}/report/pdf`

---

## Screenshots

No dashboard screenshots are checked into this repository yet. After cloning and running the stack locally, you can capture the dashboard, scan detail, findings, and regression views and add them under a `docs/screenshots/` folder if desired.

---

## Security notes

- No active penetration testing or target exploitation
- Frontend never recalculates risk scores
- JWT is not placed in URLs
- CORS origins are configurable and are not `*` for this authenticated app
- Reports do not embed secrets or API keys
- Regression matching does not use Gemini
- Production image keeps `GEMINI_API_KEY` server-side only
- On Vercel, keep secrets in project Environment Variables only (never `VITE_*`)

---

## License

This project is provided as a portfolio / educational demonstration unless otherwise specified.
