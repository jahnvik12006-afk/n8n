"""WRITE tools — require Telegram confirmation before executing."""
import asyncio
from app.tools.base import Tool
from app.youtube_client import youtube_data_client
from app.database import log_execution

# Pending confirmations: token -> {"video_id": ..., "field": ..., "old": ..., "new": ...}
_pending: dict[str, dict] = {}


def add_pending(token: str, data: dict):
    _pending[token] = data


def pop_pending(token: str) -> dict | None:
    return _pending.pop(token, None)


async def _execute_update(video_id: str, field: str, new_value: str | list):
    yt = youtube_data_client()
    video = yt.videos().list(part="snippet", id=video_id).execute()["items"][0]
    snippet = video["snippet"]

    old_value = snippet.get(field)
    snippet[field] = new_value

    yt.videos().update(
        part="snippet",
        body={"id": video_id, "snippet": snippet},
    ).execute()

    await log_execution(
        action=f"update_{field}",
        video_id=video_id,
        field=field,
        old_val=str(old_value),
        new_val=str(new_value),
    )
    return {"success": True, "video_id": video_id, "field": field, "new_value": new_value}


class UpdateTitle(Tool):
    def __init__(self):
        super().__init__(
            name="UpdateTitle",
            description="Update video title (requires Telegram confirmation)",
            permission="WRITE",
        )

    async def run(self, video_id: str, new_title: str, confirmed: bool = False, **kwargs) -> dict:
        if not confirmed:
            return {"pending": True, "video_id": video_id, "field": "title", "new_value": new_title}
        return await _execute_update(video_id, "title", new_title)


class UpdateDescription(Tool):
    def __init__(self):
        super().__init__(
            name="UpdateDescription",
            description="Update video description (requires Telegram confirmation)",
            permission="WRITE",
        )

    async def run(self, video_id: str, new_description: str, confirmed: bool = False, **kwargs) -> dict:
        if not confirmed:
            return {"pending": True, "video_id": video_id, "field": "description", "new_value": new_description}
        return await _execute_update(video_id, "description", new_description)


class UpdateTags(Tool):
    def __init__(self):
        super().__init__(
            name="UpdateTags",
            description="Update video tags (requires Telegram confirmation)",
            permission="WRITE",
        )

    async def run(self, video_id: str, new_tags: list[str], confirmed: bool = False, **kwargs) -> dict:
        if not confirmed:
            return {"pending": True, "video_id": video_id, "field": "tags", "new_value": new_tags}
        return await _execute_update(video_id, "tags", new_tags)
