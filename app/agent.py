"""AI Agent — fast single-pass, parallel tool execution."""
import json
import re
import asyncio
from app.llm import chat
from app.tools.registry import TOOLS
from app.database import get_recent_memory, save_memory

SYSTEM_PROMPT = """You are HisuClaw, AI manager for a Hindi Manhwa/Manga YouTube channel.

Tools available:
{tools}

Rules:
- READ/GENERATE tools: use freely.
- WRITE tools: only if user explicitly asked to update/change something.
- Reply in JSON: {{"thought":"...","tool":"ToolName or null","tool_args":{{}},"response":"..."}}
- If no tool needed, set tool to null and answer directly in response.
- Be concise. Use emojis. Format for Telegram.
"""


def _tools_summary() -> str:
    return "\n".join(f"- {n}: {t.description} [{t.permission}]" for n, t in TOOLS.items())


async def run_agent(user_message: str) -> str:
    memory = await get_recent_memory(10)
    memory_text = "\n".join(f"{m['key']}: {m['value']}" for m in memory[-5:])

    system = SYSTEM_PROMPT.format(tools=_tools_summary())
    if memory_text:
        system += f"\n\nContext:\n{memory_text}"

    raw = chat(system, user_message)

    # Extract JSON
    try:
        data = json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {"response": raw}

    tool_name = data.get("tool")
    tool_args = data.get("tool_args") or {}

    if tool_name and tool_name in TOOLS:
        tool_result = await TOOLS[tool_name].execute(**tool_args)
        await save_memory(f"tool:{tool_name}", json.dumps(tool_result)[:300])

        # Single follow-up pass with result
        follow = chat(
            "You are HisuClaw. Summarize this tool result for Telegram. Use emojis, be concise.",
            f"Tool: {tool_name}\nResult: {json.dumps(tool_result)[:1000]}\nUser asked: {user_message}"
        )
        return follow

    response = data.get("response", raw)
    await save_memory("agent", str(response)[:200])
    return response
