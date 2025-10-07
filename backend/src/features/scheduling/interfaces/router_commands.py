"""Command endpoints for scheduling."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import tenant_session
from ...core.security import (
    Principal,
    ensure_authorized,
    get_current_principal,
    require_any_role,
)
from ..application.command_handlers import CreateAppointmentHandler
from ..application.commands import CreateAppointmentCommand
from ..domain.value_objects import SlotMode
from ..infra.repositories import SchedulingRepository, SlotNotAvailableError
from .dto import CreateAppointmentRequest, CreateAppointmentResponse

router = APIRouter(prefix="/commands/scheduling", tags=["scheduling:commands"])

ALLOWED_ROLES = ["patient", "doctor", "secretary", "clinic_admin"]


async def get_session(
    principal: Principal = Depends(get_current_principal),
) -> AsyncSession:
    async with tenant_session(principal.tenant_id) as session:
        yield session


@router.post(
    "/appointments",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateAppointmentResponse,
    summary="Book an appointment for a slot",
)
async def create_appointment(
    payload: CreateAppointmentRequest,
    principal: Principal = Depends(require_any_role(ALLOWED_ROLES)),
    session: AsyncSession = Depends(get_session),
):
    await ensure_authorized(
        principal,
        obj="/commands/scheduling/appointments",
        act="POST",
        tenant_id=principal.tenant_id,
    )

    repository = SchedulingRepository(session)
    handler = CreateAppointmentHandler(repository)
    command = CreateAppointmentCommand(
        tenant_id=principal.tenant_id,
        slot_id=payload.slot_id,
        patient_id=payload.patient_id,
        reason=payload.reason,
        mode=payload.mode or SlotMode.ONSITE,
        requested_by=principal.sub,
    )

    try:
        appointment, _ = await handler.handle(command)
        await session.commit()
    except SlotNotAvailableError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except NoResultFound as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found") from exc
    except Exception as exc:  # pragma: no cover - defensive
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to book appointment") from exc

    return CreateAppointmentResponse.from_domain(appointment)

