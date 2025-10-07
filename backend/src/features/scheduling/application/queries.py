"""Query DTOs for scheduling."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.value_objects import SlotMode


class FetchAvailabilitiesQuery(BaseModel):
    tenant_id: str
    starts_at: datetime
    ends_at: datetime
    practitioner_id: str | None = None
    mode: SlotMode | None = Field(default=None)
