# Keur Doctor – Backend (FastAPI)

FastAPI service implementing the Keur Doctor scheduling MVP with multi-tenant isolation (PostgreSQL RLS), Keycloak authentication, and Casbin authorization. Deux parcours distincts sont gérés :

- **Patients** : auto-inscription publique via Keycloak, visibilité contrôlée par des grants patient ↔ clinique.
- **Professionnels** : accès sur invitation, MFA obligatoire, rattachement à un tenant et attribution de rôles métier.

## Prerequisites
- Python 3.11+
- Docker & Docker Compose

## Quick start
```bash
cd backend
cp .env.example .env
docker compose up --build -d
docker compose exec app alembic upgrade head
../scripts/keycloak-setup.sh   # optional helper
```

Keycloak → http://localhost:8081  
Backend → http://localhost:8000

## Environment variables
The `.env` file exposes all required settings (database URL, Keycloak realm, Casbin paths, rate limits, etc.). Update them as needed for your environment.

Variables supplémentaires clés :

- `PRO_INVITE_SECRET` / `PRO_INVITE_TTL_MINUTES` : signature et validité des liens d’invitation professionnels.
- `KC_ADMIN_CLIENT_ID` / `KC_ADMIN_CLIENT_SECRET` : client admin Keycloak utilisé pour attribuer les rôles/tenant lors de l’onboarding.
- `PRO_ONBOARDING_URL` : URL frontend vers laquelle les invitations redirigent (`https://frontend/pro/onboarding`).

## Keycloak configuration

Le script `../scripts/keycloak-setup.sh` crée automatiquement les clients et rôles nécessaires. Principales briques du realm **`keur-doctor`** :

- Clients Frontend :
  - `keur-patient-frontend` (public, PKCE) – auto-inscription activée, redirections vers `/patient`.
  - `keur-pro-frontend` (public, PKCE) – accès uniquement sur invitation, MFA à activer dans l’admin console.
- Client Backend : `keur-backend` (confidential) – expose les rôles applicatifs (`patient`, `doctor`, `nurse`, `secretary`, `clinic_admin`).
- Mappers :
  - Rôles du client `keur-backend` ajoutés dans `resource_access.keur-backend.roles`.
  - Attribut utilisateur `tenant_id` propagé dans les tokens pour les professionnels.
- Rôles par défaut : `patient` est ajouté aux « default roles » du realm afin que toute nouvelle inscription patient reçoive automatiquement ce rôle.

Pour la production, configurez deux browser flows distincts : un flow léger pour `keur-patient-frontend` (password + email vérifié) et un flow renforcé (MFA) pour `keur-pro-frontend`. Pensez également à pousser le thème `themes/keur-login` et à sélectionner "keur-login" comme Login Theme pour une interface cohérente avec le frontend.

## Authentification & contrôle d’accès
- `core/security.get_access_context` vérifie chaque JWT hors-ligne via le JWKS (cache TTL 1h) et contrôle strictement `iss`, `aud`, `alg=RS256`, `exp`, `nbf`, `iat`. Les rôles du client `keur-backend` et l’attribut `tenant_id` sont extraits pour composer un `AccessContext`.
- Les helpers `require_role` / `require_any_role` sécurisent les routes FastAPI, tandis que `ensure_authorized` délègue la décision finale à Casbin (RBAC multi-tenant).
- Casbin s’appuie sur l’adapter SQLAlchemy (`casbin_sqlalchemy_adapter`) et applique des policies domain-aware (`sub`, `tenant`, `obj`, `act`). Les Seeds initiaux sont fournis dans `casbin/seed_policy.csv`.
- Pour les routes professionnelles, `tenant_session(tenant_id)` applique `SET app.tenant_id` afin que la RLS PostgreSQL isole chaque requête.

## Casbin policies

Les politiques RBAC sont stockées dans PostgreSQL via l’adapter SQLAlchemy. Le service seed automatiquement `casbin/seed_policy.csv` lors du premier démarrage :

- Les patients peuvent consulter les disponibilités et créer des rendez-vous.
- Les rôles professionnels (`doctor`, `nurse`, `secretary`, `clinic_admin`) peuvent gérer les commandes de scheduling.
- Les `clinic_admin` disposent d’actions supplémentaires (invitations pro, endpoints d’administration, etc.).

## Observability and security

- `/healthz` returns the service status.
- `/metrics` exposes Prometheus-formatted metrics (requests, latency).
- Structured logging via `structlog`; set `STRUCTLOG_JSON=false` in `.env` for console-friendly output.
- Security headers and a 30 req/min rate limit on availability queries.

## Database & RLS

Les migrations Alembic mettent en place :

- Les tables `calendars`, `slots`, `appointments` avec RLS forcé (`tenant_id = current_setting('app.tenant_id')`).
- `patient_tenant_grants` : lien patient ↔ tenant, créé automatiquement lors du premier rendez-vous afin d’autoriser les vues croisées (clinique ↔ patient) tout en restant conforme aux règles RGPD.
- `patient_access_grants` : squelette pour les futures politiques de partage inter-tenant.

Le helper `tenant_session(tenant_id)` enveloppe chaque appel pro en exécutant `SET app.tenant_id = '<uuid>'`. Pour les patients, les filtres applicatifs s’appuient sur `sub` (identifiant utilisateur) et sur les grants enregistrés.

Un endpoint d’administration (`POST /commands/onboarding/pro-invitations`) permet aux `clinic_admin` de générer des liens d’invitation signés. L’acceptation (`POST /commands/onboarding/pro-invitations/accept`) assigne, via l’API admin Keycloak, le `tenant_id` et le rôle professionnel au compte connecté.

## Testing

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
```

## Manual API smoke test

1. Obtain an access token from Keycloak (authorization code flow via the frontend or CLI).
2. Call the API with the token:
   ```bash
   curl -H "Authorization: Bearer <token>" \
        'http://localhost:8000/queries/scheduling/availabilities?starts_at=2024-01-01T00:00:00Z&ends_at=2024-01-02T00:00:00Z'
   ```
3. Book an appointment (requires a pre-existing open slot):
   ```bash
   curl -X POST http://localhost:8000/commands/scheduling/appointments \
        -H "Authorization: Bearer <token_patient>" \
        -H "Content-Type: application/json" \
        -d '{"slot_id":"<slot-uuid>","patient_id":"<patient-sub>"}'
   ```

4. Générer une invitation professionnelle (authentifié en `clinic_admin` et rattaché à un tenant) :
   ```bash
   curl -X POST http://localhost:8000/commands/onboarding/pro-invitations \
        -H "Authorization: Bearer <token_clinic_admin>" \
        -H "Content-Type: application/json" \
        -d '{"email":"pro@example.com","role":"doctor"}'
   ```
   La réponse contient un `invite_url` à transmettre au professionnel. Ce dernier pourra finaliser son onboarding via `/pro/onboarding?token=...`, ce qui déclenchera l’attribution du tenant et du rôle côté Keycloak.
