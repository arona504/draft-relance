"""Query endpoints for scheduling."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.db import tenant_session
from ...core.http import limiter
from ...core.security import Principal, ensure_authorized, get_current_principal
from ...core.settings import get_settings
from ..application.query_handlers import FetchAvailabilitiesHandler
from ..application.queries import FetchAvailabilitiesQuery
from ..infra.repositories import SchedulingRepository
from .dto import AvailabilityDTO, AvailabilityQueryParams

router = APIRouter(prefix="/queries/scheduling", tags=["scheduling:queries"])

RATE_LIMIT = f"{get_settings().rate_limit_queries_per_min}/minute"


async def get_repository(
    principal: Principal = Depends(get_current_principal),
) -> SchedulingRepository:
    async with tenant_session(principal.tenant_id) as session:
        yield SchedulingRepository(session)


@router.get(
    "/availabilities",
    response_model=list[AvailabilityDTO],
    summary="List available slots for booking",
)
@limiter.limit(RATE_LIMIT)
async def list_availabilities(
    params: AvailabilityQueryParams = Depends(),
    principal: Principal = Depends(get_current_principal),
    repository: SchedulingRepository = Depends(get_repository),
):
    await ensure_authorized(
        principal,
        obj="/queries/scheduling/availabilities",
        act="GET",
        tenant_id=principal.tenant_id,
    )

    handler = FetchAvailabilitiesHandler(repository)
    query = FetchAvailabilitiesQuery(
        tenant_id=principal.tenant_id,
        starts_at=params.starts_at,
        ends_at=params.ends_at,
        practitioner_id=params.practitioner_id,
        mode=params.mode,
    )
    slots = await handler.handle(query)
    return [AvailabilityDTO.from_domain(slot) for slot in slots]
