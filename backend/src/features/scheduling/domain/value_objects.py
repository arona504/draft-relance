"""Value objects for the Scheduling domain."""

from __future__ import annotations

from enum import Enum


class SlotMode(str, Enum):
    ONSITE = "onsite"
    TELE = "tele"


class SlotStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"

