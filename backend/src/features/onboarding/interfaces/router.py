"""FastAPI routes handling professional onboarding invitations."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ...core.security import AccessContext, get_access_context, require_role
from ...core.settings import get_settings
from ..application.invitations import decode_invitation_token, issue_invitation_token
from ..infra.keycloak_admin import KeycloakAdminClient, KeycloakAdminError

router = APIRouter(prefix="/commands/onboarding", tags=["onboarding"])


class InvitationRequest(BaseModel):
    """Payload to generate a professional onboarding invitation."""

    email: EmailStr
    role: str


class InvitationResponse(BaseModel):
    """Response body returned when issuing an invitation."""

    invite_token: str
    invite_url: str
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    """Payload used when accepting an invitation."""

    token: str


@router.post("/pro-invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_pro_invitation(
    payload: InvitationRequest,
    context: AccessContext = Depends(require_role("clinic_admin")),
):
    """Allow a clinic administrator to generate a signed onboarding invite."""
    settings = get_settings()
    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun tenant clinique associé à l'administrateur.",
        )
    invite_token, expires_at = issue_invitation_token(
        settings=settings,
        tenant_id=context.tenant_id,
        email=payload.email,
        role=payload.role,
        invited_by=context.sub,
    )

    invite_url = f"{settings.pro_onboarding_url}?token={invite_token}"

    return InvitationResponse(
        invite_token=invite_token,
        invite_url=invite_url,
        expires_at=expires_at,
    )


@router.post("/pro-invitations/accept", status_code=status.HTTP_200_OK)
async def accept_pro_invitation(
    payload: AcceptInvitationRequest,
    context: AccessContext = Depends(get_access_context),
):
    """Finalize a professional invitation by updating Keycloak."""
    settings = get_settings()
    try:
        invitation = decode_invitation_token(payload.token, settings)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token_email = invitation.email.lower()
    context_email = str(context.claims.get("email", "")).lower()
    if context_email and context_email != token_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'adresse e-mail ne correspond pas à l'invitation",
        )

    if context.roles and invitation.role in context.roles:
        return {"status": "already-provisioned"}

    if context.tenant_id and context.tenant_id != invitation.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous êtes déjà associé à une autre clinique.",
        )

    admin_client = KeycloakAdminClient(settings)
    try:
        await admin_client.assign_pro_member(
            user_id=context.sub,
            tenant_id=invitation.tenant_id,
            role=invitation.role,
        )
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return {"status": "ok"}
