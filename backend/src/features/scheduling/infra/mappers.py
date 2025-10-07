"""Mapping helpers between ORM models and domain entities."""

from __future__ import annotations

import uuid

from ..domain.entities import Appointment as DomainAppointment
from ..domain.entities import Slot as DomainSlot
from ..domain.value_objects import AppointmentStatus, SlotMode, SlotStatus
from .models import Appointment, Slot


def generate_id() -> str:
    return str(uuid.uuid4())


def map_slot(model: Slot) -> DomainSlot:
    return DomainSlot(
        id=model.id,
        tenant_id=model.tenant_id,
        calendar_id=model.calendar_id,
        practitioner_id=model.calendar.practitioner_id if model.calendar else "",
        starts_at=model.starts_at,
        ends_at=model.ends_at,
        mode=SlotMode(model.mode),
        status=SlotStatus(model.status),
        capacity=model.capacity,
    )


def map_appointment(model: Appointment) -> DomainAppointment:
    return DomainAppointment(
        id=model.id,
        tenant_id=model.tenant_id,
        slot_id=model.slot_id,
        patient_id=model.patient_id,
        status=AppointmentStatus(model.status),
        reason=model.reason,
        mode=SlotMode(model.mode),
        created_at=model.created_at,
    )

