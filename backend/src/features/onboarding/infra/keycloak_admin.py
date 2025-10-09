"""Utility helpers to interact with the Keycloak Admin REST API."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from ...core.settings import Settings


class KeycloakAdminError(RuntimeError):
    """Raised when Keycloak admin operations fail."""


class KeycloakAdminClient:
    """Thin wrapper over Keycloak admin REST endpoints."""

    def __init__(self, settings: Settings) -> None:
        if not settings.kc_admin_client_id or not settings.kc_admin_client_secret:
            raise KeycloakAdminError(
                "KC_ADMIN_CLIENT_ID and KC_ADMIN_CLIENT_SECRET must be configured to manage invitations."
            )
        self._settings = settings
        self._backend_client_uuid: Optional[str] = None
        self._role_cache: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    @property
    def _admin_base_url(self) -> str:
        return f"{self._settings.kc_url.rstrip('/')}/admin/realms/{self._settings.kc_realm}"  # noqa: E501

    async def _obtain_admin_token(self) -> str:
        data = {
            "grant_type": "client_credentials",
            "client_id": self._settings.kc_admin_client_id,
            "client_secret": self._settings.kc_admin_client_secret,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self._settings.kc_token_url, data=data)
        if response.status_code >= 400:
            raise KeycloakAdminError("Failed to obtain Keycloak admin token")
        token = response.json().get("access_token")
        if not token:
            raise KeycloakAdminError("Admin token missing from Keycloak response")
        return token

    async def _get_backend_client_uuid(self, admin_token: str) -> str:
        async with self._lock:
            if self._backend_client_uuid:
                return self._backend_client_uuid

            params = {"clientId": self._settings.kc_client_id}
            headers = {"Authorization": f"Bearer {admin_token}"}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self._admin_base_url}/clients",
                    params=params,
                    headers=headers,
                )
            if response.status_code >= 400:
                raise KeycloakAdminError("Unable to lookup backend client in Keycloak")
            clients: list[dict[str, Any]] = response.json()
            if not clients:
                raise KeycloakAdminError("Backend client not found in Keycloak realm")
            self._backend_client_uuid = clients[0]["id"]
            return self._backend_client_uuid

    async def _get_role_representation(self, admin_token: str, role: str) -> dict[str, Any]:
        cached = self._role_cache.get(role)
        if cached:
            return cached

        client_uuid = await self._get_backend_client_uuid(admin_token)
        headers = {"Authorization": f"Bearer {admin_token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self._admin_base_url}/clients/{client_uuid}/roles/{role}",
                headers=headers,
            )
        if response.status_code >= 400:
            raise KeycloakAdminError(f"Role '{role}' not found in Keycloak")
        role_repr = response.json()
        self._role_cache[role] = role_repr
        return role_repr

    async def _update_user_attributes(self, admin_token: str, user_id: str, tenant_id: str) -> None:
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }
        payload = {"attributes": {"tenant_id": [tenant_id]}}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.put(
                f"{self._admin_base_url}/users/{user_id}",
                json=payload,
                headers=headers,
            )
        if response.status_code >= 400:
            raise KeycloakAdminError("Unable to update Keycloak user attributes")

    async def _assign_client_role(self, admin_token: str, user_id: str, role: str) -> None:
        client_uuid = await self._get_backend_client_uuid(admin_token)
        role_repr = await self._get_role_representation(admin_token, role)

        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self._admin_base_url}/users/{user_id}/role-mappings/clients/{client_uuid}",
                json=[role_repr],
                headers=headers,
            )
        if response.status_code >= 400:
            raise KeycloakAdminError("Unable to assign client role to Keycloak user")

    async def assign_pro_member(self, user_id: str, tenant_id: str, role: str) -> None:
        admin_token = await self._obtain_admin_token()
        await self._update_user_attributes(admin_token, user_id, tenant_id)
        await self._assign_client_role(admin_token, user_id, role)
