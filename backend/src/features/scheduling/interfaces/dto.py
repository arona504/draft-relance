"""DTOs for FastAPI layers."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..domain.entities import Appointment as DomainAppointment
from ..domain.entities import Slot as DomainSlot
from ..domain.value_objects import AppointmentStatus, SlotMode, SlotStatus


class AvailabilityQueryParams(BaseModel):
    starts_at: datetime
    ends_at: datetime
    practitioner_id: Optional[str] = None
    mode: Optional[SlotMode] = Field(default=None)


class AvailabilityDTO(BaseModel):
    id: str
    starts_at: datetime
    ends_at: datetime
    practitioner_id: str
    mode: SlotMode
    status: SlotStatus

    @classmethod
    def from_domain(cls, slot: DomainSlot) -> "AvailabilityDTO":
        return cls(
            id=slot.id,
            starts_at=slot.starts_at,
            ends_at=slot.ends_at,
            practitioner_id=slot.practitioner_id,
            mode=slot.mode,
            status=slot.status,
        )


class CreateAppointmentRequest(BaseModel):
    slot_id: str
    patient_id: str
    reason: Optional[str] = None
    mode: Optional[SlotMode] = None
    tenant_id: Optional[str] = None


class CreateAppointmentResponse(BaseModel):
    appointment_id: str
    status: AppointmentStatus

    @classmethod
    def from_domain(cls, appointment: DomainAppointment) -> "CreateAppointmentResponse":
        return cls(appointment_id=appointment.id, status=appointment.status)
