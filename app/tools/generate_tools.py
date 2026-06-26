"""GENERATION tools — AI + local SEO engine."""
import json
import re
from app.tools.base import Tool
from app.llm import chat
from app.seo_engine import (
    score_title, generate_tags_for_topic, full_seo_audit,
    EMOTIONAL_TRIGGERS, POWER_WORDS, HINDI_HOOKS,
)

SYSTEM = (
    "You are an expert YouTube SEO strategist for Hindi Manhwa/Manhua/Manga recap channels. "
    "Respond in JSON only. No markdown, no explanation outside JSON."
)


def _extract_json(raw: str) -> dict:
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else {"raw": raw}


class GenerateTitles(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateTitles",
            description="Generate CTR-optimized titles with SEO scores",
            permission="GENERATE",
        )

    async def run(self, topic: str, current_title: str = "", channel_title: str = "", channel_description: str = "", **kwargs) -> dict:
        channel_ctx = f"Channel: {channel_title}\nNiche: {channel_description[:200]}\n" if channel_title else ""
        current_score = score_title(current_title) if current_title else None
        prompt = (
            f"{channel_ctx}"
            f"Generate 5 CTR-optimized YouTube titles for this channel.\n"
            f"Topic/Video: {topic}\n"
            f"Current title: {current_title or 'none'}\n\n"
            f"Rules:\n"
            f"- 40-70 characters\n"
            f"- Use emotional triggers: {', '.join(EMOTIONAL_TRIGGERS[:6])}\n"
            f"- Use power words: {', '.join(POWER_WORDS[:5])}\n"
            f"- 1-2 emojis: {', '.join(HINDI_HOOKS[:4])}\n"
            f"- Match the channel niche exactly, do not guess manhwa if channel is about something else\n"
            f"- Hinglish (Hindi+English mix) for maximum Indian CTR\n"
            f'Return JSON: {{"titles": ["title1", "title2", "title3", "title4", "title5"]}}'
        )
        raw = chat(SYSTEM, prompt)
        data = _extract_json(raw)
        titles = data.get("titles", [])

        # Score each generated title
        scored = [{"title": t, **score_title(t)} for t in titles]
        scored.sort(key=lambda x: x["score"], reverse=True)

        return {
            "titles": scored,
            "current_score": current_score,
        }


class GenerateDescriptions(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateDescriptions",
            description="Generate SEO-optimized descriptions with CTA",
            permission="GENERATE",
        )

    async def run(self, title: str, topic: str, **kwargs) -> dict:
        prompt = (
            f"Generate a YouTube description for a Hindi Manhwa recap video.\n"
            f"Title: {title}\nTopic: {topic}\n\n"
            f"Must include:\n"
            f"- Hook (first 2 lines visible before 'show more')\n"
            f"- Timestamps placeholder (00:00 Intro, 02:00 Story, etc.)\n"
            f"- Subscribe CTA with bell icon\n"
            f"- 10-15 hashtags\n"
            f"- Social links placeholder\n"
            f"- Min 500 characters total\n"
            f'Return JSON: {{"description": "..."}}'
        )
        raw = chat(SYSTEM, prompt)
        data = _extract_json(raw)
        desc = data.get("description", raw)
        return {"description": desc, "char_count": len(desc)}


class GenerateTags(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateTags",
            description="Generate 25 SEO tags with local engine",
            permission="GENERATE",
        )

    async def run(self, title: str, topic: str, **kwargs) -> dict:
        # Local engine first (no API needed)
        local_tags = generate_tags_for_topic(topic)

        # LLM adds channel-specific tags
        prompt = (
            f"Generate 15 additional YouTube tags for: Title: {title}, Topic: {topic}.\n"
            f"Mix: broad (manhwa, manga), mid (manhwa hindi), long-tail (topic specific hindi recap).\n"
            f'Return JSON: {{"tags": ["tag1", ...]}}'
        )
        raw = chat(SYSTEM, prompt)
        data = _extract_json(raw)
        llm_tags = data.get("tags", [])

        combined = list(dict.fromkeys(local_tags + llm_tags))[:30]
        return {"tags": combined, "count": len(combined)}


class GenerateSeriesIdeas(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateSeriesIdeas",
            description="Trending Manhwa series ideas for Hindi audience",
            permission="GENERATE",
        )

    async def run(self, **kwargs) -> dict:
        prompt = (
            "Suggest 5 trending Manhwa/Manhua series for a Hindi YouTube recap channel in 2025.\n"
            "For each: series name, why it's trending, estimated CTR potential (high/medium/low), "
            "one title idea.\n"
            'Return JSON: {"ideas": [{"series": "...", "reason": "...", "ctr_potential": "...", "title_idea": "..."}, ...]}'
        )
        raw = chat(SYSTEM, prompt)
        return _extract_json(raw)


class GenerateContentStrategy(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateContentStrategy",
            description="Weekly and monthly content plan",
            permission="GENERATE",
        )

    async def run(self, focus: str = "growth", channel_title: str = "", channel_description: str = "", **kwargs) -> dict:
        channel_ctx = f"Channel name: {channel_title}\nChannel description: {channel_description}\n" if channel_title else ""
        prompt = (
            f"{channel_ctx}"
            f"Create a content strategy for THIS YouTube channel. Focus: {focus}.\n"
            "Base suggestions on the actual channel topic above — do NOT assume manhwa/manga unless that is the topic.\n"
            "Include: best posting days/times for Indian audience, content ideas matching the channel niche, thumbnail tips.\n"
            'Return JSON: {"weekly": [{"day": "...", "content": "...", "tags": [...], "tip": "..."}], '
            '"monthly": [{"week": 1, "theme": "...", "goal": "..."}]}'
        )
        raw = chat(SYSTEM, prompt)
        return _extract_json(raw)


class AuditSEO(Tool):
    def __init__(self):
        super().__init__(
            name="AuditSEO",
            description="Full SEO audit of a video: title, description, tags scored locally",
            permission="READ",
        )

    async def run(self, title: str = "", description: str = "", tags: list = None, **kwargs) -> dict:
        return full_seo_audit(title, description, tags or [])
