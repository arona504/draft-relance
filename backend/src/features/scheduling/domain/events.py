"""Domain events for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AppointmentBooked:
    appointment_id: str
    slot_id: str
    tenant_id: str
    occurred_at: datetime

