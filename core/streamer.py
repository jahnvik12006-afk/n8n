import uuid

import httpx

from core.bot import Bot
from core.config import config
from core.http_client import HttpClient
from core.logger import logger
from core.retry import with_retry


CDN_HEADERS = {
    "Referer": "https://moviebox.org/",
    "Origin": "https://moviebox.org",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


class _StreamBody(httpx.AsyncByteStream):
    def __init__(self, boundary: str, fields: list[tuple[str, str]], file_chunks):
        self.boundary = boundary
        self.fields = fields
        self.file_chunks = file_chunks
        self._field_bytes: list[bytes] | None = None

    async def __aiter__(self):
        for name, value in self.fields:
            yield (
                f'--{self.boundary}\r\n'
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f'{value}\r\n'
            ).encode()

        yield (
            f'--{self.boundary}\r\n'
            f'Content-Disposition: form-data; name="video"; filename="video.mp4"\r\n'
            f'Content-Type: video/mp4\r\n\r\n'
        ).encode()

        async for chunk in self.file_chunks:
            yield chunk

        yield f'\r\n--{self.boundary}--\r\n'.encode()


@with_retry()
async def stream_video_to_channel(channel_id: str, cdn_url: str, caption: str) -> bool:
    client = HttpClient.get()

    dl_resp = await client.get(cdn_url, headers=CDN_HEADERS)
    dl_resp.raise_for_status()

    boundary = uuid.uuid4().hex
    body = _StreamBody(
        boundary=boundary,
        fields=[
            ("chat_id", str(channel_id)),
            ("caption", caption),
            ("parse_mode", "HTML"),
            ("supports_streaming", "true"),
        ],
        file_chunks=dl_resp.aiter_bytes(),
    )

    bot = Bot.get()
    tg_url = f"{bot.api_base}/sendVideo"

    tg_resp = await client.post(
        tg_url,
        content=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    tg_resp.raise_for_status()
    result = tg_resp.json()
    logger.info(
        "Streamed video to %s (ok=%s)",
        channel_id, result.get("ok"),
    )
    return result.get("ok", False)
