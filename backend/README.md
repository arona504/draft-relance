# Keur Doctor – Backend (FastAPI)

FastAPI service implementing the Keur Doctor scheduling MVP with multi-tenant isolation (PostgreSQL RLS), Keycloak authentication, and Casbin authorization.

## Requirements
- Python 3.11+
- Docker & Docker Compose (for local stack)

## Getting Started
```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### Run the API
```bash
uvicorn src.main:app --reload
```

### Run with Docker
```bash
docker compose up --build
```
The stack exposes:
- FastAPI: http://localhost:8000
- PostgreSQL: localhost:5432 (db `keurnet`, user/password `postgres`)
- Keycloak: http://localhost:8081

## Database & Migrations
```bash
alembic upgrade head
```
Alembic runs against the `DATABASE_URL` set in `.env`. The initial migration creates calendars, slots, appointments, and enforces tenant isolation with row-level security (RLS).

## Authorization (Casbin)
Policies are loaded into PostgreSQL via the SQLAlchemy adapter. On first boot the adapter seeds `casbin/seed_policy.csv`. Update policies with:
```bash
python -m casbin --config casbin/model.conf casbin/seed_policy.csv
```
or by editing the DB records directly.

## Observability
- `/metrics` exposes Prometheus-formatted metrics.
- Structured JSON logs produced by `structlog`.
- Optional OTLP tracing via `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Placeholder dictation endpoint: `POST /commands/dictation/notes` (accepted for future ASR integration).

## Tests
```bash
pytest
```

## Keycloak Bootstrapping
After `docker compose up`, visit Keycloak (http://localhost:8081) and:

1. Create realm `keur-doctor`.
2. Create clients:
   - `keur-frontend` (Public, PKCE, redirect `http://localhost:3000/*`).
   - `keur-backend` (Confidential or Public, audience `keur-backend`, direct access grants enabled).
3. Create client roles on `keur-backend`: `clinic_admin`, `doctor`, `secretary`, `nurse`, `patient`.
4. Protocol mappers:
   - User attribute `tenant_id` → Token claim `tenant_id`.
   - Client roles → Token claim (default `resource_access` mapper works).
5. Create demo users and assign roles + tenant attribute (UUID string).
6. For API calls, obtain a token (password grant or Authorization Code) and call:
   ```bash
   curl -H "Authorization: Bearer <token>" \
        'http://localhost:8000/queries/scheduling/availabilities?starts_at=2024-01-01T00:00:00Z&ends_at=2024-01-02T00:00:00Z'
   ```

### PostgreSQL Tenant Context
Every request sets `SET app.tenant_id = '<tenant_uuid>'` before accessing the database. RLS policies enforce that only rows matching the tenant are visible or writable.
