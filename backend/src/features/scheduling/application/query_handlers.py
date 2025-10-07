"""Query handlers for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..domain.entities import Slot as DomainSlot
from ..infra.repositories import SchedulingRepository
from .queries import FetchAvailabilitiesQuery


@dataclass
class FetchAvailabilitiesHandler:
    repository: SchedulingRepository

    async def handle(self, query: FetchAvailabilitiesQuery) -> List[DomainSlot]:
        return await self.repository.list_availabilities(
            tenant_id=query.tenant_id,
            starts_at=query.starts_at,
            ends_at=query.ends_at,
            practitioner_id=query.practitioner_id,
            mode=query.mode,
        )

