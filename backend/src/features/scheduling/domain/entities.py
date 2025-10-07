"""Aggregate roots and entities for scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .value_objects import AppointmentStatus, SlotMode, SlotStatus


@dataclass(slots=True)
class Slot:
    id: str
    tenant_id: str
    calendar_id: str
    practitioner_id: str
    starts_at: datetime
    ends_at: datetime
    mode: SlotMode
    status: SlotStatus
    capacity: int = 1

    def is_available(self) -> bool:
        return self.status == SlotStatus.OPEN


@dataclass(slots=True)
class Appointment:
    id: str
    tenant_id: str
    slot_id: str
    patient_id: str
    status: AppointmentStatus
    reason: Optional[str] = None
    mode: SlotMode = SlotMode.ONSITE
    created_at: datetime = field(default_factory=datetime.utcnow)

