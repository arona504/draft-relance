"""Repository implementations for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..domain.entities import Appointment as DomainAppointment
from ..domain.entities import Slot as DomainSlot
from ..domain.value_objects import AppointmentStatus, SlotStatus
from . import mappers
from .models import Appointment, Slot


class SlotNotAvailableError(Exception):
    """Raised when a slot cannot be booked."""


@dataclass
class SchedulingRepository:
    session: AsyncSession

    async def list_availabilities(
        self,
        tenant_id: str,
        starts_at,
        ends_at,
        practitioner_id: str | None,
        mode,
    ) -> list[DomainSlot]:
        stmt: Select = (
            select(Slot)
            .options(joinedload(Slot.calendar))
            .where(
                Slot.tenant_id == tenant_id,
                Slot.status == SlotStatus.OPEN,
                Slot.starts_at >= starts_at,
                Slot.ends_at <= ends_at,
            )
            .order_by(Slot.starts_at)
        )

        if practitioner_id:
            stmt = stmt.where(Slot.calendar.has(practitioner_id=practitioner_id))

        if mode:
            stmt = stmt.where(Slot.mode == mode)

        result = await self.session.execute(stmt)
        slots: Sequence[Slot] = result.scalars().all()
        return [mappers.map_slot(slot) for slot in slots]

    async def create_appointment(
        self,
        tenant_id: str,
        slot_id: str,
        patient_id: str,
        reason: str | None,
        mode,
    ) -> DomainAppointment:
        stmt = select(Slot).where(Slot.id == slot_id, Slot.tenant_id == tenant_id).with_for_update()
        result = await self.session.execute(stmt)
        slot: Slot | None = result.scalars().first()
        if slot is None:
            raise NoResultFound("Slot not found")

        if slot.status != SlotStatus.OPEN:
            raise SlotNotAvailableError("Slot not available")

        appointment_count = await self.session.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.slot_id == slot_id,
                Appointment.tenant_id == tenant_id,
                Appointment.status == AppointmentStatus.BOOKED,
            )
        )
        if appointment_count is None:
            appointment_count = 0
        if appointment_count >= slot.capacity:
            raise SlotNotAvailableError("Slot capacity reached")

        appointment_model = Appointment(
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

        return mappers.map_appointment(appointment_model)

