"""Command endpoints for scheduling."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound

from src.core.db import get_session_factory, tenant_session
from src.core.security import AccessContext, ensure_authorized, require_any_role
from ..application.command_handlers import BookAppointmentHandler
from ..application.commands import BookAppointmentCommand
from ..infra.repositories import SchedulingRepository, SlotNotAvailableError
from .dto import CreateAppointmentRequest, CreateAppointmentResponse

router = APIRouter(prefix="/commands/scheduling", tags=["scheduling:commands"])

ALLOWED_ROLES = ["patient", "doctor", "secretary", "clinic_admin"]


@router.post(
    "/appointments",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateAppointmentResponse,
    summary="Book an appointment for a slot",
)
async def create_appointment(
    payload: CreateAppointmentRequest,
    context: AccessContext = Depends(require_any_role(ALLOWED_ROLES)),
):
    target_tenant = context.tenant_id or payload.tenant_id
    if target_tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id must be provided when booking en tant que patient",
        )

    await ensure_authorized(
        context,
        obj="/commands/scheduling/appointments",
        act="POST",
        tenant_id=target_tenant,
    )

    patient_id = payload.patient_id
    if "patient" in context.roles and not any(role in {"doctor", "nurse", "secretary", "clinic_admin"} for role in context.roles):
        patient_id = context.sub

    if context.tenant_id:
        session_context = tenant_session(target_tenant)
    else:
        session_factory = get_session_factory()
        session_context = session_factory()

    async with session_context as session:
        repository = SchedulingRepository(session)
        handler = BookAppointmentHandler(repository)
        command = BookAppointmentCommand(
            tenant_id=target_tenant,
            slot_id=payload.slot_id,
            patient_id=patient_id,
            reason=payload.reason,
            mode=payload.mode,
            requested_by=context.sub,
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to book appointment",
            ) from exc

    return CreateAppointmentResponse.from_domain(appointment)
