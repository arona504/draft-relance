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
1. Configure Keycloak (see below, or run `scripts/keycloak-setup.sh`).
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
Run the automated helper (requires the stack to be up):
```bash
./scripts/keycloak-setup.sh
```

Or perform the steps manually:
1. Create realm **`keur-doctor`** et activez l’option *Registration* pour les patients.
2. Clients :
   - `keur-patient-frontend` (Public, PKCE) – redirect `http://localhost:3000/api/auth/callback/keycloak-patient` + `http://localhost:3000/*`.
   - `keur-pro-frontend` (Public, PKCE) – redirect `http://localhost:3000/api/auth/callback/keycloak-pro` + `http://localhost:3000/*`.
   - `keur-backend` (Confidential, service accounts) – audience de l’API.
3. Protocol mappers sur `keur-backend` :
   - Attribut utilisateur `tenant_id` → claim `tenant_id`.
   - Rôles client → claim `resource_access.keur-backend.roles`.
4. Rôles disponibles : `patient`, `doctor`, `nurse`, `secretary`, `clinic_admin`. Ajoutez `patient` au rôle par défaut `default-roles-keur-doctor`.
5. Créez les comptes de démonstration `clinic_admin@demo`, `doctor1@demo`, `sec1@demo` (mot de passe `Passw0rd!`) et attribuez-les au tenant de test.
6. Activez un flow MFA renforcé pour le client professionnel et conservez un flow léger pour le client patient.

## Casbin policies
Policies live in PostgreSQL via the SQLAlchemy adapter. On first boot the service seeds `backend/casbin/seed_policy.csv`, granting:
- `patient` : consultation & réservation de créneaux
- `doctor` / `nurse` / `secretary` : gestion des commandes scheduling
- `clinic_admin` : actions supplémentaires (invitations professionnelles, endpoints d’administration)

## Observability & security
- JSON structured logs via structlog
- Rate limiting (SlowAPI) on scheduling queries
- Prometheus metrics at `/metrics`
- Security headers & optional OTLP tracing

## Testing
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run lint && npm run build`

## Next steps
1. Extend domain contexts (clinical records, sharing, dictation).
2. Add event bus & messaging for CQRS projections.
3. Harden token refresh (Keycloak Service Accounts) & add e2e tests.

## Verification commands
```bash
# Backend stack, migrations, and Keycloak seed
cd backend
docker compose up --build -d
docker compose exec app alembic upgrade head
../scripts/keycloak-setup.sh

# Frontend dev server
cd ../frontend
npm install
npm run dev
```
Visitez http://localhost:3000, choisissez l’espace **Patient** ou **Professionnel**, connectez-vous avec un compte de démonstration ou via une invitation, puis simulez une réservation de créneau. Les métriques restent accessibles via `curl http://localhost:8000/healthz` et `curl http://localhost:8000/metrics`.
