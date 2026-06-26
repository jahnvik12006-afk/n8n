"""AI Agent — conversation memory + Hindi support."""
import json
import re
from app.llm import chat
from app.tools.registry import TOOLS
from app.database import get_recent_memory, save_memory

SYSTEM_PROMPT = """You are HisuClaw, expert AI manager for a Hindi Manhwa/Manga YouTube channel.

Tools available:
{tools}

Rules:
- Always reply in the SAME language the user used (Hindi/Hinglish/English). Never switch languages.
- Use tools ONLY when user explicitly asks for data ("channel dikhao", "videos analyze karo", "growth check karo").
- For advice/tips questions ("kya karu", "kaise badhao", "suggest karo", "improvement chahiye") — answer directly from expertise, NO tool needed.
- Give specific, actionable YouTube advice: thumbnails, title hooks, posting time, shorts strategy, hashtags, engagement tactics.
- WRITE tools: only when user says "update kar" / "change kar" AND confirms. First generate suggestion, then ask confirmation.
- Never dump raw data as an answer. Interpret and explain.
- Reply ONLY in JSON: {{"thought":"...","tool":"ToolName or null","tool_args":{{}},"response":"..."}}
"""


def _tools_summary() -> str:
    return "\n".join(f"- {n}: {t.description} [{t.permission}]" for n, t in TOOLS.items())


async def run_agent(user_message: str) -> str:
    # Load last 8 memory entries as conversation context
    memory = await get_recent_memory(8)
    conv = "\n".join(f"{m['key']}: {m['value']}" for m in memory)

    system = SYSTEM_PROMPT.format(tools=_tools_summary())
    if conv:
        system += f"\n\nRecent conversation:\n{conv}"

    raw = chat(system, user_message)

    # Extract JSON — handle <think> tags from reasoning models
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    try:
        data = json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {"response": raw}

    tool_name = data.get("tool")
    tool_args = data.get("tool_args") or {}

    # Save user message to memory
    await save_memory("user", user_message[:200])

    if tool_name and tool_name in TOOLS:
        tool_result = await TOOLS[tool_name].execute(**tool_args)
        await save_memory(f"tool:{tool_name}", json.dumps(tool_result)[:400])

        follow = chat(
            f"You are HisuClaw. Reply in the same language as the user (user said: '{user_message}'). "
            "Summarize tool result clearly for Telegram. No JSON, plain text. Be concise.",
            f"Tool: {tool_name}\nResult: {json.dumps(tool_result)[:1500]}\nUser asked: {user_message}"
        )
        # Strip <think> from follow-up too
        follow = re.sub(r"<think>.*?</think>", "", follow, flags=re.DOTALL).strip()
        await save_memory("bot", follow[:200])
        return follow

    response = data.get("response", raw)
    await save_memory("bot", str(response)[:200])
    return str(response)
