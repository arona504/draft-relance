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
With the stack running you can let the helper script provision the realm, clients, mappers, roles, and demo users:
```bash
../scripts/keycloak-setup.sh
```

The script creates:
- Realm `keur-doctor`
- Clients `keur-frontend` (public PKCE) & `keur-backend` (confidential audience)
- Protocol mappers exposing `tenant_id` and client roles
- Roles `clinic_admin`, `doctor`, `secretary`, `nurse`, `patient`
- Users `clinic_admin@demo`, `doctor1@demo`, `sec1@demo` with password `Passw0rd!` and tenant `tenant-0001`

Manual setup steps mirror the automation above if you prefer the Keycloak UI. Once tokens are issued you can call:
```bash
curl -H "Authorization: Bearer <token>" \
  'http://localhost:8000/queries/scheduling/availabilities?starts_at=2024-01-01T00:00:00Z&ends_at=2024-01-02T00:00:00Z'
```

### PostgreSQL Tenant Context
Every request sets `SET app.tenant_id = '<tenant_uuid>'` before accessing the database. RLS policies enforce that only rows matching the tenant are visible or writable, with an additional cross-tenant read policy scaffolded around `patient_access_grants` for future sharing scenarios.
