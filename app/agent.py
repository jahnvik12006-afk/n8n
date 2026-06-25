"""AI Agent — orchestrates tool calls via Groq LLM."""
import json
from app.llm import chat
from app.tools.registry import TOOLS
from app.database import get_recent_memory, save_memory

SYSTEM_PROMPT = """You are HisuClaw, an AI agent managing a Hindi Manhwa/Manga YouTube channel.

You have access to the following tools:
{tools}

Rules:
- You may call READ and GENERATE tools freely.
- WRITE tools require explicit user confirmation via Telegram.
- Never modify channel data without confirmation.
- Always respond in JSON with keys: "thought", "tool" (optional), "tool_args" (optional), "response".
- If no tool needed, set "tool" to null and give direct "response".
"""


def _tools_summary() -> str:
    return "\n".join(
        f"- {name}: {t.description} [permission={t.permission}]"
        for name, t in TOOLS.items()
    )


async def run_agent(user_message: str) -> str:
    memory = await get_recent_memory(20)
    memory_text = "\n".join(f"[{m['created_at']}] {m['key']}: {m['value']}" for m in memory)

    system = SYSTEM_PROMPT.format(tools=_tools_summary())
    if memory_text:
        system += f"\n\nRecent memory (last 24h):\n{memory_text}"

    raw = chat(system, user_message)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON block
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {"response": raw}

    tool_name = data.get("tool")
    tool_args = data.get("tool_args", {})

    if tool_name and tool_name in TOOLS:
        tool = TOOLS[tool_name]
        tool_result = await tool.execute(**tool_args)
        await save_memory(f"tool:{tool_name}", json.dumps(tool_result)[:500])

        # Second LLM pass to interpret tool result
        follow_up = chat(
            system,
            f"Tool {tool_name} returned:\n{json.dumps(tool_result)}\n\nUser asked: {user_message}\n\nProvide a clear, helpful response.",
        )
        try:
            follow_data = json.loads(follow_up)
            return follow_data.get("response", follow_up)
        except Exception:
            return follow_up

    response = data.get("response", raw)
    await save_memory("agent_response", str(response)[:500])
    return response
