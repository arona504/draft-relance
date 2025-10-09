# Keur Doctor – Frontend (Next.js)

Next.js 14 App Router client pour Keur Doctor. L’interface propose deux parcours d’authentification distincts :

- **Patients** – auto-inscription publique via Keycloak, accès à `/app/patient/*`.
- **Professionnels de santé** – accès sur invitation, MFA obligatoire, rattachement à un tenant clinique, accès à `/app/pro/*`.

Tous les appels vers l’API FastAPI transitent par une couche BFF (`/api/bff/*`) qui insère les jetons côté serveur : aucun token n’est exposé au navigateur.

## Prérequis
- Node.js 18+
- npm / pnpm / yarn (les exemples ci-dessous utilisent npm)

## Installation & lancement
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```
L’application est disponible sur http://localhost:3000.

## Variables d’environnement
| Variable | Description |
| --- | --- |
| `NEXTAUTH_URL` | URL publique du frontend (`http://localhost:3000`). |
| `NEXTAUTH_SECRET` | Chaîne aléatoire pour chiffrer la session NextAuth. |
| `KEYCLOAK_ISSUER` | Issuer Keycloak (`http://localhost:8081/realms/keur-doctor`). |
| `KEYCLOAK_PATIENT_CLIENT_ID` / `KEYCLOAK_PATIENT_CLIENT_SECRET` | Client public (PKCE) pour le parcours patient. |
| `KEYCLOAK_PRO_CLIENT_ID` / `KEYCLOAK_PRO_CLIENT_SECRET` | Client public (PKCE) pour le parcours professionnel. |
| `KEYCLOAK_BACKEND_CLIENT_ID` | Client audience utilisé pour extraire les rôles. |
| `KEYCLOAK_TOKEN_ENDPOINT` | Endpoint token/refresh du realm. |
| `API_BASE` | URL de l’API FastAPI (`http://localhost:8000`). |

## NextAuth & providers
- Deux providers Keycloak sont déclarés dans `lib/auth.ts` :
  - `keycloak-patient` (client `keur-patient-frontend`, auto-inscription activée).
  - `keycloak-pro` (client `keur-pro-frontend`, MFA obligatoire, invitation requise).
- Les callbacks `jwt`/`session` décodent l’`access_token` côté serveur pour exposer les rôles (`patient`, `doctor`, `nurse`, `secretary`, `clinic_admin`) et le `tenantId` aux composants serveur — aucun jeton n’est injecté dans la session envoyée au navigateur.
- Les rôles professionnels définissent également `session.user.type = "pro"` afin de simplifier les redirections.

## Parcours d’authentification

### Patients
- Page d’entrée : `GET /patient` (maquette shadcn/ui “Login 02”).
- Boutons : *Se connecter* (SSO via `signIn("keycloak-patient")`) et *Créer un compte* (redirection vers la page de registre Keycloak patient).
- Après connexion, redirection vers `/app/patient`.

### Professionnels
- Page d’entrée : `GET /pro` (maquette shadcn/ui dédiée aux équipes de soins).
- Bouton : *Se connecter (Professionnel)* (`signIn("keycloak-pro")`).
- Lien *Demander un accès* → mailto support (pas d’auto-inscription).
- Onboarding : `/pro/onboarding?token=...` (lien signé généré par un `clinic_admin`). Après validation, l’utilisateur est redirigé vers `/app/pro`.

### Middleware & autorisation
- `/app/patient/*` : nécessite une session avec le rôle `patient` (sinon redirection vers `/patient`).
- `/app/pro/*` : nécessite un rôle parmi `doctor`, `nurse`, `secretary`, `clinic_admin` (sinon redirection vers `/pro`).
- `/app/pro/admin/*` : réservé aux `clinic_admin`.
- Toute ressource non autorisée renvoie vers la porte d’entrée appropriée.

## BFF & appels API
- Les appels front→API passent par `/api/bff/*` (ex. `/api/bff/appointments`, `/api/bff/pro/invitations` et `/api/bff/pro/invitations/accept`).
- Chaque handler récupère la session (`getServerSession`) puis extrait le JWT via `getToken` (cookies HTTP only) pour injecter l’en-tête `Authorization` côté serveur.
- Aucun `fetch` direct vers l’API n’est effectué côté navigateur ; les tokens ne quittent jamais le code serveur Next.js.

## Keycloak – rappel de configuration

Consultez `scripts/keycloak-setup.sh` pour créer automatiquement le realm `keur-doctor` avec :
- `keur-patient-frontend` (auto-inscription, flow léger) ;
- `keur-pro-frontend` (accès sur invitation, MFA à activer) ;
- `keur-backend` (audience API) + mappers (`tenant_id`, `resource_access.keur-backend.roles`).

Le script ajoute le rôle `patient` aux rôles par défaut du realm, ce qui attribue automatiquement ce rôle à toute nouvelle inscription.

## Lint & build
```bash
npm run lint
npm run build
```
