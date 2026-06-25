"""Report generator — triggered by /reports endpoint or Telegram /report."""
import json
from app.tools.read_tools import AnalyzeVideos, AnalyzeGrowth, AnalyzeCompetitors
from app.llm import chat
from app.database import save_report, save_memory

SYSTEM = "You are HisuClaw. Generate a concise YouTube channel performance report in plain text for Telegram."


async def generate_report() -> str:
    videos_tool = AnalyzeVideos()
    growth_tool = AnalyzeGrowth()

    videos_data = await videos_tool.execute(max_results=10)
    growth_data = await growth_tool.execute(days=28)

    top3 = videos_data.get("videos", [])[:3]
    best = top3[0] if top3 else {}
    worst = min(videos_data.get("videos", [{}]), key=lambda v: v.get("views", 0), default={})

    prompt = f"""
Channel Growth (28d): {json.dumps(growth_data.get('growth_data', [])[:5])}
Top Videos: {json.dumps(top3)}
Best Video: {json.dumps(best)}
Worst Video: {json.dumps(worst)}

Generate a report including:
- Views summary
- CTR insights
- Retention insights
- Growth summary
- Best video
- Worst video
- Competitor insights (general advice for Hindi Manhwa channel)
- Suggested next topic
- Suggested title style
Keep it under 600 words, formatted for Telegram.
"""
    report_text = chat(SYSTEM, prompt)
    await save_report(report_text)
    await save_memory("last_report", report_text[:500])
    return report_text
