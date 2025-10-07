# Keur Doctor – SaaS Scheduling Platform

Two sibling projects (FastAPI backend + Next.js frontend) implementing the Keur Doctor MVP: multi-tenant scheduling with Keycloak authentication, Casbin authorization, CQRS, and BFF architecture.

```
.
├── backend   # FastAPI + PostgreSQL + Casbin + Alembic
└── frontend  # Next.js 14 + NextAuth + shadcn/ui
```

## Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

## Quick start
1. Configure Keycloak (see below).
2. From `backend/`:
   ```bash
   cp .env.example .env
   docker compose up --build
   ```
3. Apply migrations:
   ```bash
   docker compose exec app alembic upgrade head
   ```
4. From `frontend/`:
   ```bash
   cp .env.local.example .env.local
   npm install
   npm run dev
   ```

Backend runs on http://localhost:8000, Frontend on http://localhost:3000, Keycloak on http://localhost:8081.

## Keycloak bootstrap checklist
1. Create realm **`keur-doctor`**.
2. Clients:
   - `keur-frontend` (Public, PKCE, redirect `http://localhost:3000/*`).
   - `keur-backend` (Confidential or public; audience `keur-backend`).
3. Protocol mappers:
   - User attribute `tenant_id` → token claim `tenant_id`.
   - Client roles of `keur-backend` → keep default mapper (`resource_access`).
4. Roles on `keur-backend`: `clinic_admin`, `doctor`, `secretary`, `nurse`, `patient`.
5. Demo users with `tenant_id` (UUID string) and assigned roles.

## Casbin policies
Policies live in PostgreSQL via the SQLAlchemy adapter. On first boot the service seeds `backend/casbin/seed_policy.csv`, granting:
- `patient`: read availabilities & book appointments
- `doctor` / `secretary`: book appointments
- `clinic_admin`: full scheduling access

## Observability & security
- JSON structured logs via structlog
- Rate limiting (SlowAPI) on scheduling queries
- Prometheus metrics at `/metrics`
- Security headers & optional OTLP tracing

## Testing
- Backend: `cd backend && pytest`
- Frontend: rely on Next.js lint/build (`npm run lint`, `npm run build`)

## Next steps
1. Extend domain contexts (clinical records, sharing, dictation).
2. Add event bus & messaging for CQRS projections.
3. Harden token refresh (Keycloak Service Accounts) & add e2e tests.
