from fastapi import APIRouter

from app.schemas.analyzer import AnalyzerResult
from app.schemas.common import AnalyzeRequest
from app.services.analyzer import build_preview

router = APIRouter(tags=["analyzer"])


@router.post("/analyze", response_model=AnalyzerResult)
@router.post("/analyzer/preview", response_model=AnalyzerResult)
async def analyzer_preview(payload: AnalyzeRequest) -> AnalyzerResult:
    """Validate a public URL and identify its platform without fetching content."""
    return await build_preview(str(payload.url))
