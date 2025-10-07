"""Command DTOs for scheduling."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..domain.value_objects import SlotMode


class BookAppointmentCommand(BaseModel):
    tenant_id: str
    slot_id: str
    patient_id: str
    reason: str | None = None
    mode: SlotMode | None = Field(default=None)
    requested_by: str
