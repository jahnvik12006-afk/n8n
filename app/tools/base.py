"""MCP-style tool base class."""
from dataclasses import dataclass, field
from typing import Any
import json
from app.database import log_tool


@dataclass
class Tool:
    name: str
    description: str
    permission: str  # READ | WRITE | GENERATE
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)

    async def run(self, **kwargs) -> Any:
        raise NotImplementedError

    async def execute(self, **kwargs) -> Any:
        result = await self.run(**kwargs)
        await log_tool(self.name, json.dumps(kwargs), json.dumps(result) if not isinstance(result, str) else result)
        return result
