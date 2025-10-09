#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
BACKEND_DIR="${SCRIPT_DIR}/../backend"
COMPOSE_CMD=${COMPOSE_CMD:-docker compose}
KEYCLOAK_SERVICE=${KEYCLOAK_SERVICE:-keycloak}
KEYCLOAK_SERVER=${KEYCLOAK_SERVER:-http://localhost:8081}
REALM=${KEYCLOAK_REALM:-keur-doctor}
ADMIN_USER=${KEYCLOAK_ADMIN:-admin}
ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:-admin}
TENANT_UUID=${TENANT_UUID:-tenant-0001}
FRONTEND_REDIRECT=${FRONTEND_REDIRECT:-http://localhost:3000/*}

compose() {
  (cd "$BACKEND_DIR" && ${COMPOSE_CMD} "$@")
}

kc() {
  compose exec -T "${KEYCLOAK_SERVICE}" /opt/keycloak/bin/kcadm.sh "$@"
}

printf '\n===> Configuring Keycloak realm %s\n' "${REALM}"

kc config credentials \
  --server "${KEYCLOAK_SERVER}" \
  --realm master \
  --user "${ADMIN_USER}" \
  --password "${ADMIN_PASSWORD}"

kc create realms -s realm="${REALM}" -s enabled=true || true

kc update realms/${REALM} \
  -s registrationAllowed=true \
  -s resetPasswordAllowed=true \
  -s rememberMe=true || true

FRONTEND_BASE=${FRONTEND_BASE:-http://localhost:3000}
PATIENT_CLIENT_ID=keur-patient-frontend
PRO_CLIENT_ID=keur-pro-frontend
BACKEND_CLIENT_ID=keur-backend

kc create clients -r "${REALM}" \
  -s clientId=${PATIENT_CLIENT_ID} \
  -s protocol=openid-connect \
  -s publicClient=true \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=false \
  -s serviceAccountsEnabled=false || true

kc create clients -r "${REALM}" \
  -s clientId=${PRO_CLIENT_ID} \
  -s protocol=openid-connect \
  -s publicClient=true \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=false \
  -s serviceAccountsEnabled=false || true

kc create clients -r "${REALM}" \
  -s clientId=${BACKEND_CLIENT_ID} \
  -s protocol=openid-connect \
  -s publicClient=false \
  -s secret=backend-secret \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=true \
  -s serviceAccountsEnabled=true || true

get_client_id() {
  local client_id="$1"
  kc get clients -r "${REALM}" -q clientId="${client_id}" | grep '"id"' | head -n1 | cut -d '"' -f4
}

PATIENT_ID=$(get_client_id ${PATIENT_CLIENT_ID})
PRO_ID=$(get_client_id ${PRO_CLIENT_ID})
BACKEND_ID=$(get_client_id ${BACKEND_CLIENT_ID})

kc update "clients/${PATIENT_ID}" -r "${REALM}" \
  -s 'attributes."pkce.code.challenge.method"=S256' \
  -s 'redirectUris=["'"${FRONTEND_BASE}/api/auth/callback/keycloak-patient"'", "'"${FRONTEND_BASE}/*"'"]' \
  -s 'webOrigins=["'"${FRONTEND_BASE}"'"]'

kc update "clients/${PRO_ID}" -r "${REALM}" \
  -s 'attributes."pkce.code.challenge.method"=S256' \
  -s 'redirectUris=["'"${FRONTEND_BASE}/api/auth/callback/keycloak-pro"'", "'"${FRONTEND_BASE}/*"'"]' \
  -s 'webOrigins=["'"${FRONTEND_BASE}"'"]'

kc update "clients/${BACKEND_ID}" -r "${REALM}" \
  -s publicClient=false \
  -s serviceAccountsEnabled=true \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=true \
  -s 'attributes."use.refresh.tokens"=true'

# Protocol mappers backend
kc create "clients/${BACKEND_ID}/protocol-mappers/models" -r "${REALM}" \
  -s name="tenant-id" \
  -s protocol="openid-connect" \
  -s protocolMapper="oidc-usermodel-attribute-mapper" \
  -s 'config."user.attribute"=tenant_id' \
  -s 'config."claim.name"=tenant_id' \
  -s 'config."jsonType.label"=String' \
  -s 'config."id.token.claim"=true' \
  -s 'config."access.token.claim"=true' \
  -s 'config."userinfo.token.claim"=true' || true

kc create "clients/${BACKEND_ID}/protocol-mappers/models" -r "${REALM}" \
  -s name="backend-client-roles" \
  -s protocol="openid-connect" \
  -s protocolMapper="oidc-usermodel-client-role-mapper" \
  -s 'config."clientId"='"${BACKEND_CLIENT_ID}" \
  -s 'config."claim.name"=resource_access.'"${BACKEND_CLIENT_ID}"'.roles' \
  -s 'config."jsonType.label"=String' \
  -s 'config."id.token.claim"=true' \
  -s 'config."access.token.claim"=true' \
  -s 'config."userinfo.token.claim"=true' || true

for role in clinic_admin doctor nurse secretary patient; do
  kc create "clients/${BACKEND_ID}/roles" -r "${REALM}" -s name="$role" || true
done

# Ajout du rôle patient aux rôles par défaut
kc add-roles -r "${REALM}" --rname "default-roles-${REALM}" --cclientid ${BACKEND_CLIENT_ID} --rolename patient || true

# Comptes de démonstration professionnels
create_pro_user() {
  local username="$1"
  local role="$2"
  kc create users -r "${REALM}" -s username="${username}" -s enabled=true -s email="${username}" || true
  local user_id
  user_id=$(kc get users -r "${REALM}" -q username="${username}" | grep '"id"' | head -n1 | cut -d '"' -f4)
  kc update "users/${user_id}" -r "${REALM}" -s 'attributes.tenant_id=["'"${TENANT_UUID}"'"]'
  kc set-password -r "${REALM}" --userid "${user_id}" --new-password "Passw0rd!" --temporary=false
  kc add-roles -r "${REALM}" --uusername "${username}" --cclientid ${BACKEND_CLIENT_ID} --rolename "${role}" || true
}

create_pro_user "clinic_admin@demo" "clinic_admin"
create_pro_user "doctor1@demo" "doctor"
create_pro_user "sec1@demo" "secretary"

cat <<INFO

Keycloak realm '${REALM}' ready.

Clients créés :
  - ${PATIENT_CLIENT_ID} (public, auto-inscription patient via ${FRONTEND_BASE}/patient)
  - ${PRO_CLIENT_ID} (public, invitation uniquement via ${FRONTEND_BASE}/pro)
  - ${BACKEND_CLIENT_ID} (audience API)

Le rôle "patient" est attribué automatiquement à toute nouvelle inscription.
MFA et politiques renforcées doivent être configurées côté client professionnel depuis l'Admin Console.

Identifiants de démonstration (mot de passe 'Passw0rd!') :
  clinic_admin@demo, doctor1@demo, sec1@demo

INFO
