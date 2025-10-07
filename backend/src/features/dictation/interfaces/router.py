"""Placeholder endpoints for future dictation services."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from ....core.security import AccessContext, ensure_authorized, require_any_role

router = APIRouter(prefix="/commands/dictation", tags=["dictation"])

ALLOWED_ROLES = ["doctor", "clinic_admin", "secretary"]


@router.post("/notes", status_code=status.HTTP_202_ACCEPTED, summary="Placeholder dictation endpoint")
async def submit_dictation(
    payload: Dict[str, Any],
    context: AccessContext = Depends(require_any_role(ALLOWED_ROLES)),
):
    await ensure_authorized(
        context,
        obj="/commands/dictation/notes",
        act="POST",
        tenant_id=context.tenant_id,
    )
    return {
        "status": "accepted",
        "message": "Dictation processing is not yet implemented",
        "payload": payload,
    }
