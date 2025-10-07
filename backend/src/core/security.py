"""Security helpers for authentication (Keycloak) and authorization (Casbin)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterable

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from jwt import PyJWKClient

from .casbin_enforcer import get_enforcer
from .settings import Settings, get_settings


class TokenError(HTTPException):
    """Raised when a token is invalid."""

    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED) -> None:
        super().__init__(status_code=status_code, detail=detail)


@dataclass(slots=True)
class Principal:
    """Represents the authenticated user."""

    sub: str
    tenant_id: str
    roles: list[str]
    raw_token: str
    preferred_username: str | None = None

    def has_any_role(self, required_roles: Iterable[str]) -> bool:
        required = {role.lower() for role in required_roles}
        return any(role.lower() in required for role in self.roles)


class KeycloakTokenVerifier:
    """Validate JWT access tokens issued by Keycloak."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jwk_client = PyJWKClient(settings.kc_jwks_url)

    async def verify(self, token: str) -> dict:
        signing_key = await asyncio.to_thread(self._jwk_client.get_signing_key_from_jwt, token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.settings.kc_audience,
            issuer=self.settings.kc_issuer,
            leeway=self.settings.jwt_leeway_seconds,
        )


@lru_cache(1)
def get_token_verifier(settings: Settings | None = None) -> KeycloakTokenVerifier:
    """Return a cached verifier instance."""
    settings = settings or get_settings()
    return KeycloakTokenVerifier(settings)


async def get_current_principal(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Extract and validate the current principal from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise TokenError("Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = await get_token_verifier(settings).verify(token)
    except jwt.PyJWTError as exc:  # pragma: no cover - defensive
        raise TokenError("Invalid access token") from exc

    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise TokenError("Missing tenant_id claim")

    resource_access = claims.get("resource_access", {})
    client_access = resource_access.get(settings.kc_client_id, {})
    roles = client_access.get("roles", [])
    if not isinstance(roles, list):
        roles = []

    preferred_username = claims.get("preferred_username")

    principal = Principal(
        sub=claims.get("sub"),
        tenant_id=tenant_id,
        roles=[role.lower() for role in roles],
        raw_token=token,
        preferred_username=preferred_username,
    )

    request.state.principal = principal
    return principal


def require_any_role(required_roles: Iterable[str]) -> Callable[[Principal], Principal]:
    """Return a dependency that ensures the principal has any of the required roles."""

    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.has_any_role(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires any of roles: {', '.join(required_roles)}",
            )
        return principal

    return dependency


async def ensure_authorized(
    principal: Principal,
    obj: str,
    act: str,
    tenant_id: str | None = None,
) -> None:
    """Check authorization via Casbin for the principal."""
    enforcer = await get_enforcer()
    domain = tenant_id or principal.tenant_id

    subjects = [principal.sub] + principal.roles

    for subject in subjects:
        allowed = await run_in_threadpool(enforcer.enforce, subject, domain, obj, act)
        if allowed:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorised to perform this action",
    )

