# Keur Doctor – Frontend (Next.js)

Next.js 14 App Router client for Keur Doctor with Keycloak SSO, NextAuth, shadcn/ui, and a BFF proxy to the FastAPI backend.

## Requirements
- Node.js 18+
- pnpm / npm / yarn (examples below use npm)

## Setup
```bash
cp .env.local.example .env.local
npm install
npm run dev
```
The development server runs on http://localhost:3000.

### Environment variables
Edit `.env.local` with the values below:
- `NEXTAUTH_URL` – public URL of the frontend.
- `NEXTAUTH_SECRET` – random string for JWT encryption.
- `KEYCLOAK_ISSUER` – `http://localhost:8081/realms/keur-doctor`.
- `KEYCLOAK_CLIENT_ID` – `keur-frontend` (public PKCE client).
- `KEYCLOAK_CLIENT_SECRET` – optional, leave empty for public client.
- `KEYCLOAK_BACKEND_CLIENT_ID` – `keur-backend` (used to extract roles from tokens).
- `KEYCLOAK_TOKEN_ENDPOINT` – token endpoint for refresh tokens.
- `API_BASE` – BFF target, e.g. `http://localhost:8000`.

## Keycloak configuration recap
1. Realm `keur-doctor` with clients `keur-frontend` (public, PKCE) and `keur-backend` (confidential or public).
2. Enable protocol mappers:
   - User attribute `tenant_id` → token claim `tenant_id`.
   - Client roles of `keur-backend` included in `resource_access`.
3. Assign roles (`clinic_admin`, `doctor`, `secretary`, `nurse`, `patient`) to demo users.
4. Set redirect URIs: `http://localhost:3000/*`.

## BFF proxy
Requests from the UI to `/api/bff/*` are executed server-side with the Keycloak access token stored in the NextAuth session—never exposed to the browser. Example:
```bash
curl -X POST http://localhost:3000/api/bff/appointments \
  -H 'Cookie: next-auth.session-token=...' \
  -d '{"slot_id":"uuid","patient_id":"uuid"}'
```

## Guarded routes
- `/` – login (shadcn/ui styles, Keycloak button).
- `/app` – tenant dashboard (authenticated).
- `/app/admin` – requires role `clinic_admin` (middleware + server guard).

## Linting & build
```bash
npm run lint
npm run build
```
