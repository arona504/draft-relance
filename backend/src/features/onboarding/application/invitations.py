"""Invitation handling for professional onboarding."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from pydantic import BaseModel, EmailStr

from ...core.settings import Settings

PRO_ROLES: set[str] = {"doctor", "nurse", "secretary", "clinic_admin"}


class InvitationTokenPayload(BaseModel):
    email: EmailStr
    role: Literal["doctor", "nurse", "secretary", "clinic_admin"]
    tenant_id: str
    invited_by: str
    exp: int
    iat: int
    aud: str


def issue_invitation_token(
    *,
    settings: Settings,
    tenant_id: str,
    email: str,
    role: str,
    invited_by: str,
) -> tuple[str, datetime]:
    role_normalised = role.strip().lower()
    if role_normalised not in PRO_ROLES:
        raise ValueError(f"Unsupported role '{role}'. Must be one of {sorted(PRO_ROLES)}")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.pro_invite_ttl_minutes)

    payload = {
        "email": email.strip().lower(),
        "role": role_normalised,
        "tenant_id": tenant_id,
        "invited_by": invited_by,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "aud": settings.pro_invite_audience,
    }

    token = jwt.encode(payload, settings.pro_invite_secret, algorithm="HS256")
    return token, expires_at


def decode_invitation_token(token: str, settings: Settings) -> InvitationTokenPayload:
    try:
        data = jwt.decode(
            token,
            settings.pro_invite_secret,
            algorithms=["HS256"],
            audience=settings.pro_invite_audience,
        )
    except jwt.PyJWTError as exc:  # pragma: no cover - defensive
        raise ValueError("Invalid invitation token") from exc

    try:
        return InvitationTokenPayload(**data)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError("Malformed invitation token") from exc
