from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SearchServiceDep, SettingsDep
from app.domain.models import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search the web for a keyword and return the top pages with extracted content",
)
async def search(
    service: SearchServiceDep,
    settings: SettingsDep,
    q: Annotated[str, Query(min_length=1, max_length=256, description="Keyword or phrase to search")],
    limit: Annotated[int | None, Query(ge=1, le=10, description="Number of links to fetch (default 5)")] = None,
) -> SearchResponse:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Query must not be blank")
    effective_limit = min(limit or settings.default_result_limit, settings.max_result_limit)
    return await service.search(query, effective_limit)
