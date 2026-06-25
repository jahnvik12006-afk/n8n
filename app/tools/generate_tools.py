"""GENERATION tools — AI-powered content generation."""
from app.tools.base import Tool
from app.llm import chat

SYSTEM = (
    "You are an expert YouTube SEO strategist for Hindi Manhwa/Manhua/Manga recap channels. "
    "Respond in JSON format only."
)


class GenerateTitles(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateTitles",
            description="Generate CTR-optimized titles for Hindi audience",
            permission="GENERATE",
        )

    async def run(self, topic: str, current_title: str = "", **kwargs) -> dict:
        prompt = (
            f"Generate 5 CTR-optimized YouTube titles for a Hindi Manhwa/Manga recap channel.\n"
            f"Topic: {topic}\n"
            f"Current title: {current_title}\n"
            "Return JSON: {{\"titles\": [\"...\", ...]}}"
        )
        result = chat(SYSTEM, prompt)
        return {"raw": result}


class GenerateDescriptions(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateDescriptions",
            description="Generate SEO-optimized descriptions",
            permission="GENERATE",
        )

    async def run(self, title: str, topic: str, **kwargs) -> dict:
        prompt = (
            f"Generate an SEO-optimized YouTube description for a Hindi Manhwa recap video.\n"
            f"Title: {title}\nTopic: {topic}\n"
            "Include keywords, hashtags, timestamps placeholder. Return JSON: {{\"description\": \"...\"}}"
        )
        result = chat(SYSTEM, prompt)
        return {"raw": result}


class GenerateTags(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateTags",
            description="Generate SEO tags",
            permission="GENERATE",
        )

    async def run(self, title: str, topic: str, **kwargs) -> dict:
        prompt = (
            f"Generate 20 SEO YouTube tags for a Hindi Manhwa recap: Title: {title}, Topic: {topic}.\n"
            "Return JSON: {{\"tags\": [\"...\", ...]}}"
        )
        result = chat(SYSTEM, prompt)
        return {"raw": result}


class GenerateSeriesIdeas(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateSeriesIdeas",
            description="New series ideas and trending recap topics",
            permission="GENERATE",
        )

    async def run(self, **kwargs) -> dict:
        prompt = (
            "Suggest 5 new trending Manhwa/Manhua/Manga recap series ideas for a Hindi YouTube channel. "
            "Return JSON: {{\"ideas\": [{{\"title\": ..., \"reason\": ...}}, ...]}}"
        )
        result = chat(SYSTEM, prompt)
        return {"raw": result}


class GenerateContentStrategy(Tool):
    def __init__(self):
        super().__init__(
            name="GenerateContentStrategy",
            description="Weekly and monthly content plan",
            permission="GENERATE",
        )

    async def run(self, focus: str = "growth", **kwargs) -> dict:
        prompt = (
            f"Create a weekly and monthly content strategy for a Hindi Manhwa/Manga recap YouTube channel. "
            f"Focus: {focus}. "
            "Return JSON: {{\"weekly\": [...], \"monthly\": [...]}}"
        )
        result = chat(SYSTEM, prompt)
        return {"raw": result}
