from fastapi import APIRouter, Depends, Body
from app.auth import require_auth
from app.tools.registry import TOOLS

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.get("/channel")
async def analyze_channel(_=Depends(require_auth)):
    return await TOOLS["AnalyzeChannel"].execute()


@router.get("/videos")
async def analyze_videos(max_results: int = 20, _=Depends(require_auth)):
    return await TOOLS["AnalyzeVideos"].execute(max_results=max_results)


@router.get("/video/{video_id}")
async def analyze_video(video_id: str, _=Depends(require_auth)):
    return await TOOLS["AnalyzeVideo"].execute(video_id=video_id)


@router.get("/retention")
async def analyze_retention(video_id: str | None = None, _=Depends(require_auth)):
    return await TOOLS["AnalyzeRetention"].execute(video_id=video_id)


@router.get("/ctr")
async def analyze_ctr(_=Depends(require_auth)):
    return await TOOLS["AnalyzeCTR"].execute()


@router.get("/audience")
async def analyze_audience(_=Depends(require_auth)):
    return await TOOLS["AnalyzeAudience"].execute()


@router.get("/growth")
async def analyze_growth(days: int = 28, _=Depends(require_auth)):
    return await TOOLS["AnalyzeGrowth"].execute(days=days)


@router.get("/seo")
async def analyze_seo(_=Depends(require_auth)):
    return await TOOLS["AnalyzeSEO"].execute()


@router.post("/competitors")
async def analyze_competitors(channel_ids: list[str] = Body(...), _=Depends(require_auth)):
    return await TOOLS["AnalyzeCompetitors"].execute(channel_ids=channel_ids)
