"""Command handlers for scheduling."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.events import AppointmentBooked
from .commands import BookAppointmentCommand
from ..domain.entities import Appointment as DomainAppointment
from ..domain.value_objects import SlotMode
from ..infra.repositories import SchedulingRepository, SlotNotAvailableError


@dataclass
class BookAppointmentHandler:
    repository: SchedulingRepository

    async def handle(self, command: BookAppointmentCommand) -> tuple[DomainAppointment, AppointmentBooked]:
        appointment = await self.repository.create_appointment(
            tenant_id=command.tenant_id,
            slot_id=command.slot_id,
            patient_id=command.patient_id,
            reason=command.reason,
            mode=command.mode or SlotMode.ONSITE,
        )
        event = AppointmentBooked(
            appointment_id=appointment.id,
            slot_id=appointment.slot_id,
            tenant_id=appointment.tenant_id,
            occurred_at=appointment.created_at,
        )
        return appointment, event
