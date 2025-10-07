#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD=${COMPOSE_CMD:-docker compose}
KEYCLOAK_SERVICE=${KEYCLOAK_SERVICE:-keycloak}
KEYCLOAK_SERVER=${KEYCLOAK_SERVER:-http://localhost:8081}
REALM=${KEYCLOAK_REALM:-keur-doctor}
ADMIN_USER=${KEYCLOAK_ADMIN:-admin}
ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:-admin}
TENANT_UUID=${TENANT_UUID:-tenant-0001}
FRONTEND_REDIRECT=${FRONTEND_REDIRECT:-http://localhost:3000/*}

kc() {
  ${COMPOSE_CMD} exec -T "${KEYCLOAK_SERVICE}" /opt/keycloak/bin/kcadm.sh "$@"
}

printf '\n===> Configuring Keycloak realm %s\n' "${REALM}"

kc config credentials \
  --server "${KEYCLOAK_SERVER}" \
  --realm master \
  --user "${ADMIN_USER}" \
  --password "${ADMIN_PASSWORD}"

kc create realms -s realm="${REALM}" -s enabled=true || true

kc create clients -r "${REALM}" \
  -s clientId=keur-frontend \
  -s protocol=openid-connect \
  -s publicClient=true \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=false || true

kc create clients -r "${REALM}" \
  -s clientId=keur-backend \
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

FRONTEND_ID=$(get_client_id keur-frontend)
BACKEND_ID=$(get_client_id keur-backend)

kc update "clients/${FRONTEND_ID}" -r "${REALM}" \
  -s 'attributes."pkce.code.challenge.method"=S256' \
  -s 'redirectUris=["'"${FRONTEND_REDIRECT}"'"]' \
  -s 'webOrigins=["http://localhost:3000"]'

kc update "clients/${BACKEND_ID}" -r "${REALM}" \
  -s publicClient=false \
  -s serviceAccountsEnabled=true \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=true \
  -s 'attributes."use.refresh.tokens"=true'

# Protocol mapper: user attribute tenant_id => claim tenant_id
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

# Protocol mapper: expose client roles under resource_access.keur-backend.roles
kc create "clients/${BACKEND_ID}/protocol-mappers/models" -r "${REALM}" \
  -s name="backend-client-roles" \
  -s protocol="openid-connect" \
  -s protocolMapper="oidc-usermodel-client-role-mapper" \
  -s 'config."clientId"=keur-backend' \
  -s 'config."claim.name"=resource_access.keur-backend.roles' \
  -s 'config."jsonType.label"=String' \
  -s 'config."id.token.claim"=true' \
  -s 'config."access.token.claim"=true' \
  -s 'config."userinfo.token.claim"=true' || true

for role in clinic_admin doctor secretary nurse patient; do
  kc create "clients/${BACKEND_ID}/roles" -r "${REALM}" -s name="$role" || true
done

create_user() {
  local username="$1"
  local email="$1"
  local role="$2"
  kc create users -r "${REALM}" -s username="${username}" -s enabled=true -s email="${email}" || true
  local user_id
  user_id=$(kc get users -r "${REALM}" -q username="${username}" | grep '"id"' | head -n1 | cut -d '"' -f4)
  kc update "users/${user_id}" -r "${REALM}" -s 'attributes.tenant_id=["'"${TENANT_UUID}"'"]'
  kc set-password -r "${REALM}" --userid "${user_id}" --new-password "Passw0rd!" --temporary=false
  kc add-roles -r "${REALM}" --uusername "${username}" --cclientid keur-backend --rolename "${role}"
}

create_user "clinic_admin@demo" "clinic_admin"
create_user "doctor1@demo" "doctor"
create_user "sec1@demo" "secretary"

cat <<INFO

Keycloak realm '${REALM}' ready.
Demo credentials use password 'Passw0rd!'.

To obtain a token (Authorization Code flow):
1. Open browser: ${KEYCLOAK_SERVER}/realms/${REALM}/protocol/openid-connect/auth?client_id=keur-frontend&response_type=code&redirect_uri=http://localhost:3000/api/auth/callback/keycloak&scope=openid%20profile%20email%20offline_access
2. Authenticate with a demo user.
3. Capture the redirected code and exchange it:
   curl -X POST ${KEYCLOAK_SERVER}/realms/${REALM}/protocol/openid-connect/token \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'grant_type=authorization_code' \
     -d 'client_id=keur-frontend' \
     -d 'code=YOUR_CODE' \
     -d 'redirect_uri=http://localhost:3000/api/auth/callback/keycloak'
INFO
