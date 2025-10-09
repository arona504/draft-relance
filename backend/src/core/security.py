"""Security helpers for authentication (Keycloak) and authorization (Casbin)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable

import jwt
from cachetools import TTLCache
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWK, PyJWKClient

from .casbin_enforcer import authorize
from .settings import Settings, get_settings

_SIGNING_KEY_CACHE: TTLCache = TTLCache(maxsize=64, ttl=3600)
_JWK_CLIENT_CACHE: dict[str, PyJWKClient] = {}
_bearer_scheme = HTTPBearer(auto_error=False)


class TokenError(HTTPException):
    """Raised when a bearer token is invalid."""

    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED) -> None:
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


@dataclass(slots=True)
class AccessContext:
    """Represents the authenticated user context extracted from a JWT."""

    sub: str
    tenant_id: str | None
    roles: list[str]
    token: str
    claims: dict[str, object]

    def has_any_role(self, expected: Iterable[str]) -> bool:
        expected_lower = {role.lower() for role in expected}
        return any(role in expected_lower for role in self.roles)


def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    client = _JWK_CLIENT_CACHE.get(jwks_url)
    if client is None:
        client = PyJWKClient(jwks_url)
        _JWK_CLIENT_CACHE[jwks_url] = client
    return client


async def _get_signing_key(token: str, settings: Settings) -> PyJWK:
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    alg = headers.get("alg")
    if not kid or alg != "RS256":
        raise TokenError("Unsupported token header")

    cache_key = (settings.kc_jwks_url, kid)
    signing_key = _SIGNING_KEY_CACHE.get(cache_key)
    if signing_key is not None:
        return signing_key

    client = _get_jwk_client(settings.kc_jwks_url)
    signing_key = await asyncio.to_thread(client.get_signing_key_from_jwt, token)
    _SIGNING_KEY_CACHE[cache_key] = signing_key
    return signing_key


async def get_access_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AccessContext:
    """Extract the AccessContext from the Authorization header."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise TokenError("Missing bearer token")

    token = credentials.credentials
    try:
        signing_key = await _get_signing_key(token, settings)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.kc_audience,
            issuer=settings.kc_issuer,
            leeway=settings.jwt_leeway_seconds,
            options={"require": ["exp", "iat", "nbf"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid access token") from exc

    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise TokenError("Missing subject")

    tenant_id_raw = claims.get("tenant_id") or claims.get("tenantId")
    tenant_id = tenant_id_raw if isinstance(tenant_id_raw, str) else None

    roles: set[str] = set()
    resource_access = claims.get("resource_access") or {}
    if isinstance(resource_access, dict):
        client_info = resource_access.get(settings.kc_client_id, {})
        client_roles = client_info.get("roles")
        if isinstance(client_roles, list):
            roles.update(role.lower() for role in client_roles if isinstance(role, str))

    fallback_roles = claims.get("roles")
    if isinstance(fallback_roles, list):
        roles.update(role.lower() for role in fallback_roles if isinstance(role, str))

    context = AccessContext(
        sub=sub,
        tenant_id=tenant_id,
        roles=sorted(roles),
        token=token,
        claims=claims,
    )
    request.state.access_context = context
    return context


def require_any_role(expected_roles: Iterable[str]):
    """FastAPI dependency that ensures the principal owns at least one role."""

    async def dependency(context: AccessContext = Depends(get_access_context)) -> AccessContext:
        if not context.has_any_role(expected_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires any of roles: {', '.join(expected_roles)}",
            )
        return context

    return dependency


def require_role(role: str):
    """FastAPI dependency enforcing a single role."""

    return require_any_role([role])


async def ensure_authorized(
    context: AccessContext,
    obj: str,
    act: str,
    tenant_id: str | None = None,
) -> None:
    """Check authorization via Casbin using both the user id and their roles."""
    domain = tenant_id or context.tenant_id or "*"
    if await authorize(context.sub, domain, obj, act):
        return

    for role in context.roles:
        if await authorize(role, domain, obj, act):
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorised to perform this action",
    )
