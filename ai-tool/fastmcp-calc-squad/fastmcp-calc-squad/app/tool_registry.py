from __future__ import annotations

import os
import sys
from functools import partial
from typing import Any, Callable, Dict, List

from agent_squad.utils import AgentTool, AgentTools

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp_client import MCPBridge


def _schema_to_properties_and_required(schema: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    if not schema:
        return {}, []
    if schema.get("type") != "object":
        return {"value": schema}, ["value"]
    return schema.get("properties", {}), schema.get("required", [])

async def build_agent_tools_from_mcp(mcp: MCPBridge) -> AgentTools:
    tools_meta = await mcp.list_tools()
    agent_tools: List[AgentTool] = []
    for tm in tools_meta:
        name = tm["name"]
        desc = tm.get("description") or f"MCP tool '{name}'"
        props, required = _schema_to_properties_and_required(tm.get("input_schema"))

        async def _caller(_name: str, **kwargs):
            return await mcp.call(_name, kwargs)

        func: Callable[..., Any] = partial(_caller, name)

        tool = AgentTool(
            name=name,
            description=desc,
            func=func,
            properties=props,
            required=required
        )
        agent_tools.append(tool)

    return AgentTools(agent_tools)
