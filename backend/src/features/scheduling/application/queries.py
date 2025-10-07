"""Query DTOs for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..domain.value_objects import SlotMode


@dataclass(slots=True)
class FetchAvailabilitiesQuery:
    tenant_id: str
    starts_at: datetime
    ends_at: datetime
    practitioner_id: Optional[str]
    mode: Optional[SlotMode]

