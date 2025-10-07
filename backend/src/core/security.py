"""Security helpers for authentication (Keycloak) and authorization (Casbin)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterable

import jwt
from cachetools import TTLCache
from fastapi import Depends, Header, HTTPException, Request, status

from .casbin_enforcer import authorize
from .settings import Settings, get_settings

_SIGNING_KEY_CACHE = TTLCache(maxsize=32, ttl=3600)  # 1 hour TTL for JWKS keys


class TokenError(HTTPException):
    """Raised when a token is invalid."""

    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED) -> None:
        super().__init__(status_code=status_code, detail=detail)


@dataclass(slots=True)
class AccessContext:
    """Represents the authenticated and authorised subject."""

    sub: str
    tenant_id: str
    roles: list[str]
    raw_token: str
    preferred_username: str | None = None

    def has_any_role(self, required_roles: Iterable[str]) -> bool:
        required = {role.lower() for role in required_roles}
        return any(role.lower() in required for role in self.roles)


class KeycloakTokenVerifier:
    """Validate JWT access tokens issued by Keycloak with cached JWKS."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jwk_client = jwt.PyJWKClient(settings.kc_jwks_url)

    async def _get_signing_key(self, token: str) -> jwt.PyJWK:
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        if not kid:
            raise TokenError("Token missing kid header")

        try:
            return _SIGNING_KEY_CACHE[kid]
        except KeyError:
            signing_key = await asyncio.to_thread(self._jwk_client.get_signing_key_from_jwt, token)
            _SIGNING_KEY_CACHE[kid] = signing_key
            return signing_key

    async def verify(self, token: str) -> dict:
        signing_key = await self._get_signing_key(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.settings.kc_audience,
            issuer=self.settings.kc_issuer,
            leeway=self.settings.jwt_leeway_seconds,
            options={"require": ["exp", "iat", "nbf"]},
        )


@lru_cache(1)
def get_token_verifier(settings: Settings | None = None) -> KeycloakTokenVerifier:
    """Return a cached verifier instance."""
    settings = settings or get_settings()
    return KeycloakTokenVerifier(settings)


async def get_access_context(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> AccessContext:
    """Extract and validate the current subject from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise TokenError("Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = await get_token_verifier(settings).verify(token)
    except jwt.PyJWTError as exc:  # pragma: no cover - defensive
        raise TokenError("Invalid access token") from exc

    issuer = claims.get("iss")
    if issuer != settings.kc_issuer:
        raise TokenError("Invalid issuer")

    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise TokenError("Missing tenant_id claim")

    resource_access = claims.get("resource_access", {})
    client_access = resource_access.get(settings.kc_client_id, {})
    roles = client_access.get("roles", [])
    if not isinstance(roles, list):
        roles = []

    preferred_username = claims.get("preferred_username")

    context = AccessContext(
        sub=str(claims.get("sub")),
        tenant_id=tenant_id,
        roles=[role.lower() for role in roles],
        raw_token=token,
        preferred_username=preferred_username,
    )

    request.state.access_context = context
    return context


def require_any_role(required_roles: Iterable[str]) -> Callable[[AccessContext], AccessContext]:
    """Return a dependency enforcing that the subject owns any of the provided roles."""

    async def dependency(context: AccessContext = Depends(get_access_context)) -> AccessContext:
        if not context.has_any_role(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires any of roles: {', '.join(required_roles)}",
            )
        return context

    return dependency


def require_role(role: str) -> Callable[[AccessContext], AccessContext]:
    """Dependency enforcing a single role."""

    return require_any_role([role])


async def ensure_authorized(
    context: AccessContext,
    obj: str,
    act: str,
    tenant_id: str | None = None,
) -> None:
    """Check authorization via Casbin for the subject and fallback roles."""
    domain = tenant_id or context.tenant_id

    if await authorize(context.sub, domain, obj, act):
        return

    for role in context.roles:
        if await authorize(role, domain, obj, act):
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorised to perform this action",
    )

