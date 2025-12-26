from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

from fastmcp import Client

# Set up logger for MCP operations
logger = logging.getLogger(__name__)


class MCPBridge:
    def __init__(self, server_script: Path):
        self._server_script = str(server_script)

    async def list_tools(self) -> List[dict]:
        async with Client(self._server_script) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            logger.info(f"📋 Available MCP tools: {tool_names}")
            return [{
                "name": t.name,
                "description": getattr(t, "description", None) or "",
                "input_schema": getattr(t, "inputSchema", None) or {
                    "type": "object", "properties": {}
                },
            } for t in tools]

    async def call(self, tool_name: str, args: Dict[str, Any]) -> str:
        logger.info(f"🔧 Calling MCP tool: '{tool_name}' with args: {args}")
        
        async with Client(self._server_script) as client:
            result = await client.call_tool(tool_name, args or {})
            raw_result = result.data if result.data is not None else (
                result.structured_content or (
                    result.content[0].text if result.content else None
                )
            )
            # Convert result to string to ensure compatibility with Bedrock
            final_result = str(raw_result) if raw_result is not None else "No result"
            logger.info(f"✅ Tool '{tool_name}' returned: {final_result}")
            return final_result
