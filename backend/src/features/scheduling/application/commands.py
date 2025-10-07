"""Command DTOs for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..domain.value_objects import SlotMode


@dataclass(slots=True)
class CreateAppointmentCommand:
    tenant_id: str
    slot_id: str
    patient_id: str
    reason: Optional[str]
    mode: Optional[SlotMode]
    requested_by: str

