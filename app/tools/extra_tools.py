"""Extra tools — Viral Hook, Thumbnail Text, Title A/B, Shorts, Comment Reply, Daily Brief, Competitor Spy."""
import json
import re
from app.tools.base import Tool
from app.llm import chat


def _j(raw: str) -> dict:
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else {"raw": raw}


def _llm(prompt: str) -> dict:
    return _j(chat("You are an expert YouTube strategist for Hindi channels. Reply in JSON only.", prompt))


# ── 1. Viral Hook Generator ────────────────────────────────────────────────

class GenerateViralHook(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateViralHook",
            description="Generate 3 viral opening hooks (first 30s script) for a video topic",
            permission="GENERATE",
        )

    async def run(self, topic: str, channel_title: str = "", **kwargs) -> dict:
        return _llm(
            f"Channel: {channel_title}\nTopic: {topic}\n"
            "Generate 3 viral Hindi YouTube opening hooks (first 30 seconds). "
            "Each hook must create curiosity, use pattern interrupt. "
            'JSON: {"hooks": [{"hook": "...", "style": "curiosity|shock|question", "why": "..."}]}'
        )


# ── 2. Thumbnail Text Generator ───────────────────────────────────────────

class GenerateThumbnailText(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateThumbnailText",
            description="Generate 3 thumbnail text options with CTR psychology",
            permission="GENERATE",
        )

    async def run(self, topic: str, channel_title: str = "", **kwargs) -> dict:
        return _llm(
            f"Channel: {channel_title}\nTopic: {topic}\n"
            "Generate 3 YouTube thumbnail text options. Rules: max 4 words each, Hindi/Hinglish preferred, "
            "create curiosity or shock, use numbers if relevant. "
            'JSON: {"options": [{"text": "...", "psychology": "...", "ctr_reason": "..."}]}'
        )


# ── 3. Title A/B Test ─────────────────────────────────────────────────────

class CompareTitles(Tool):
    def __init__(self):
        super().__init__(
            name="CompareTitles",
            description="Compare two titles and predict which will get higher CTR with reasons",
            permission="GENERATE",
        )

    async def run(self, title_a: str, title_b: str, channel_title: str = "", channel_description: str = "", **kwargs) -> dict:
        ch_ctx = f"Channel: {channel_title}\nNiche: {channel_description[:150]}\n" if channel_title else ""
        return _llm(
            f"{ch_ctx}Title A: {title_a}\nTitle B: {title_b}\n"
            "Compare these two YouTube titles. Analyze: keyword strength, curiosity gap, length, emotion. "
            'JSON: {"winner": "A or B", "score_a": 0-100, "score_b": 0-100, '
            '"reasons_a": ["..."], "reasons_b": ["..."], "improved": "best combined version"}'
        )


# ── 4. Shorts Idea Generator ──────────────────────────────────────────────

class GenerateShortsIdeas(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateShortsIdeas",
            description="Generate 5 YouTube Shorts ideas with 60-second script outline",
            permission="GENERATE",
        )

    async def run(self, topic: str, channel_title: str = "", **kwargs) -> dict:
        return _llm(
            f"Channel: {channel_title}\nTopic/Niche: {topic}\n"
            "Generate 5 YouTube Shorts ideas. Each should be 60 seconds max, high retention, trending angle. "
            'JSON: {"shorts": [{"title": "...", "hook": "first 3 seconds", "outline": "...", "hashtags": ["..."]}]}'
        )


# ── 5. Comment Reply Generator ────────────────────────────────────────────

class GenerateCommentReplies(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateCommentReplies",
            description="Generate smart, engaging replies to YouTube comments",
            permission="GENERATE",
        )

    async def run(self, comments: list, channel_title: str = "", **kwargs) -> dict:
        comments_text = "\n".join(f"- {c}" for c in comments[:10])
        return _llm(
            f"Channel: {channel_title}\nComments:\n{comments_text}\n"
            "Generate a smart, engaging Hindi/Hinglish reply for each comment. "
            "Replies should encourage engagement, feel personal, not robotic. "
            'JSON: {"replies": [{"comment": "...", "reply": "..."}]}'
        )


# ── 6. Daily Brief ────────────────────────────────────────────────────────

class GenerateDailyBrief(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateDailyBrief",
            description="Generate a daily action brief: what to upload today, best time, content tip",
            permission="GENERATE",
        )

    async def run(self, channel_title: str = "", channel_description: str = "",
                  subscribers: int = 0, recent_views: int = 0, **kwargs) -> dict:
        return _llm(
            f"Channel: {channel_title}\nNiche: {channel_description[:200]}\n"
            f"Subscribers: {subscribers}  Recent views: {recent_views}\n"
            "Generate a daily action brief for this YouTube channel. "
            "Include: best upload time today, one content idea, one SEO tip, one engagement tip. "
            'JSON: {"upload_time": "HH:MM", "content_idea": "...", "seo_tip": "...", '
            '"engagement_tip": "...", "motivation": "one line Hindi motivation"}'
        )


# ── 7. Competitor Spy ─────────────────────────────────────────────────────

class SpyCompetitor(Tool):
    def __init__(self):
        super().__init__(
            name="SpyCompetitor",
            description="Analyze a competitor YouTube channel by URL and extract their winning strategy",
            permission="READ",
        )

    async def run(self, channel_url: str, **kwargs) -> dict:
        import httpx, re as _re
        # Extract channel ID or handle from URL
        handle = _re.search(r'@([\w.-]+)', channel_url)
        channel_id_match = _re.search(r'channel/(UC[\w-]+)', channel_url)

        from app.youtube_client import youtube_data_client
        yt = youtube_data_client()

        if handle:
            resp = yt.search().list(part="snippet", q=handle.group(0), type="channel", maxResults=1).execute()
            if not resp.get("items"):
                return {"error": "Channel not found"}
            cid = resp["items"][0]["snippet"]["channelId"]
        elif channel_id_match:
            cid = channel_id_match.group(1)
        else:
            return {"error": "Invalid channel URL. Use @handle or /channel/UC... format"}

        # Fetch channel info
        ch = yt.channels().list(part="snippet,statistics", id=cid).execute()["items"][0]
        subs = int(ch["statistics"].get("subscriberCount", 0))
        views = int(ch["statistics"].get("viewCount", 0))

        # Fetch top 10 videos
        playlist_id = yt.channels().list(part="contentDetails", id=cid).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        items = yt.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=10).execute().get("items", [])
        vids = yt.videos().list(
            part="snippet,statistics",
            id=",".join(i["contentDetails"]["videoId"] for i in items)
        ).execute().get("items", [])

        top_videos = [
            {"title": v["snippet"]["title"], "views": int(v["statistics"].get("viewCount", 0)),
             "tags": v["snippet"].get("tags", [])[:5]}
            for v in sorted(vids, key=lambda x: int(x["statistics"].get("viewCount", 0)), reverse=True)
        ]

        # LLM strategy analysis
        analysis = _llm(
            f"Competitor channel: {ch['snippet']['title']}\nSubs: {subs:,}  Views: {views:,}\n"
            f"Top videos: {json.dumps(top_videos[:5])}\n"
            "Analyze their winning strategy. What titles/topics work? What can we learn? "
            'JSON: {"strategy": "...", "winning_patterns": ["..."], "content_gaps": ["..."], "steal_ideas": ["..."]}'
        )

        return {
            "channel_name": ch["snippet"]["title"],
            "subscribers": subs,
            "total_views": views,
            "top_videos": top_videos,
            **analysis,
        }
