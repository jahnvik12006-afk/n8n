from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import require_auth
from app.tools.registry import TOOLS

router = APIRouter(prefix="/api", tags=["update"])


class TitleRequest(BaseModel):
    video_id: str
    new_title: str
    confirmed: bool = False


class DescriptionRequest(BaseModel):
    video_id: str
    new_description: str
    confirmed: bool = False


class TagsRequest(BaseModel):
    video_id: str
    new_tags: list[str]
    confirmed: bool = False


@router.post("/update-title")
async def update_title(req: TitleRequest, _=Depends(require_auth)):
    return await TOOLS["UpdateTitle"].execute(**req.model_dump())


@router.post("/update-description")
async def update_description(req: DescriptionRequest, _=Depends(require_auth)):
    return await TOOLS["UpdateDescription"].execute(**req.model_dump())


@router.post("/update-tags")
async def update_tags(req: TagsRequest, _=Depends(require_auth)):
    return await TOOLS["UpdateTags"].execute(**req.model_dump())
