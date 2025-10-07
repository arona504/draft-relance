"""Query endpoints for scheduling."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.db import tenant_session
from ...core.http import limiter
from ...core.security import AccessContext, ensure_authorized, get_access_context
from ...core.settings import get_settings
from ..application.query_handlers import FetchAvailabilitiesHandler
from ..application.queries import FetchAvailabilitiesQuery
from ..infra.repositories import SchedulingRepository
from .dto import AvailabilityDTO, AvailabilityQueryParams

router = APIRouter(prefix="/queries/scheduling", tags=["scheduling:queries"])

RATE_LIMIT = f"{get_settings().rate_limit_queries_per_min}/minute"


async def get_repository(
    context: AccessContext = Depends(get_access_context),
) -> SchedulingRepository:
    async with tenant_session(context.tenant_id) as session:
        yield SchedulingRepository(session)


@router.get(
    "/availabilities",
    response_model=list[AvailabilityDTO],
    summary="List available slots for booking",
)
@limiter.limit(RATE_LIMIT)
async def list_availabilities(
    params: AvailabilityQueryParams = Depends(),
    context: AccessContext = Depends(get_access_context),
    repository: SchedulingRepository = Depends(get_repository),
):
    await ensure_authorized(
        context,
        obj="/queries/scheduling/availabilities",
        act="GET",
        tenant_id=context.tenant_id,
    )

    handler = FetchAvailabilitiesHandler(repository)
    query = FetchAvailabilitiesQuery(
        tenant_id=context.tenant_id,
        starts_at=params.starts_at,
        ends_at=params.ends_at,
        practitioner_id=params.practitioner_id,
        mode=params.mode,
    )
    slots = await handler.handle(query)
    return [AvailabilityDTO.from_domain(slot) for slot in slots]
