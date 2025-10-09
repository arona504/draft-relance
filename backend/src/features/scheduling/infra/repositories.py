"""Repository implementations for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..domain.entities import Appointment as DomainAppointment
from ..domain.entities import Slot as DomainSlot
from ..domain.value_objects import AppointmentStatus, SlotMode, SlotStatus
from . import mappers
from .models import AppointmentDB, SlotDB, PatientTenantGrantDB


class SlotNotAvailableError(Exception):
    """Raised when a slot cannot be booked."""


@dataclass
class SchedulingRepository:
    session: AsyncSession

    async def list_availabilities(
        self,
        tenant_id: str,
        starts_at: datetime,
        ends_at: datetime,
        practitioner_id: str | None,
        mode: SlotMode | None,
    ) -> list[DomainSlot]:
        stmt: Select = (
            select(SlotDB)
            .options(joinedload(SlotDB.calendar))
            .where(
                SlotDB.tenant_id == tenant_id,
                SlotDB.status == SlotStatus.OPEN,
                SlotDB.starts_at >= starts_at,
                SlotDB.ends_at <= ends_at,
            )
            .order_by(SlotDB.starts_at)
        )

        if practitioner_id:
            stmt = stmt.where(SlotDB.calendar.has(practitioner_id=practitioner_id))

        if mode:
            stmt = stmt.where(SlotDB.mode == mode)

        result = await self.session.execute(stmt)
        slots: Sequence[SlotDB] = result.scalars().all()
        return [mappers.map_slot(slot) for slot in slots]

    async def create_appointment(
        self,
        tenant_id: str,
        slot_id: str,
        patient_id: str,
        reason: str | None,
        mode: SlotMode | None,
    ) -> DomainAppointment:
        stmt = select(SlotDB).where(SlotDB.id == slot_id, SlotDB.tenant_id == tenant_id).with_for_update()
        result = await self.session.execute(stmt)
        slot: SlotDB | None = result.scalars().first()
        if slot is None:
            raise NoResultFound("Slot not found")

        if slot.status != SlotStatus.OPEN:
            raise SlotNotAvailableError("Slot not available")

        appointment_count = await self.session.scalar(
            select(func.count(AppointmentDB.id)).where(
                AppointmentDB.slot_id == slot_id,
                AppointmentDB.tenant_id == tenant_id,
                AppointmentDB.status == AppointmentStatus.BOOKED,
            )
        )
        if appointment_count is None:
            appointment_count = 0
        if appointment_count >= slot.capacity:
            raise SlotNotAvailableError("Slot capacity reached")

        appointment_model = AppointmentDB(
            id=mappers.generate_id(),
            tenant_id=tenant_id,
            slot_id=slot_id,
            patient_id=patient_id,
            status=AppointmentStatus.BOOKED,
            reason=reason,
            mode=mode or slot.mode,
        )

        slot.status = SlotStatus.CLOSED if appointment_count + 1 >= slot.capacity else slot.status

        self.session.add(appointment_model)
        await self.session.flush()

        await self._ensure_patient_grant(patient_id=patient_id, tenant_id=tenant_id)
        return mappers.map_appointment(appointment_model)

    async def _ensure_patient_grant(self, patient_id: str, tenant_id: str) -> None:
        exists = await self.session.scalar(
            select(PatientTenantGrantDB.patient_user_id).where(
                PatientTenantGrantDB.patient_user_id == patient_id,
                PatientTenantGrantDB.tenant_id == tenant_id,
            )
        )
        if exists:
            return

        grant = PatientTenantGrantDB(
            patient_user_id=patient_id,
            tenant_id=tenant_id,
            scope="appointments",
        )
        self.session.add(grant)
