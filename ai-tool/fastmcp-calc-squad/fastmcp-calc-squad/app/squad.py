from __future__ import annotations

import os
import sys
from pathlib import Path

import boto3
from agent_squad.agents import BedrockLLMAgent, BedrockLLMAgentOptions
from agent_squad.orchestrator import AgentSquad, AgentSquadConfig

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mcp_client import MCPBridge
from app.tool_registry import build_agent_tools_from_mcp

ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER = ROOT / "mcp_server" / "server.py"
PROMPT_FILE = ROOT / "app" / "prompts" / "calc_system_prompt.txt"

async def build_orchestrator() -> AgentSquad:
    region = os.getenv("AWS_REGION", "us-east-1")
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    bedrock_client = boto3.client("bedrock-runtime", region_name=region)

    orchestrator = AgentSquad(options=AgentSquadConfig(
        USE_DEFAULT_AGENT_IF_NONE_IDENTIFIED=True,
        LOG_AGENT_CHAT=True,
        LOG_EXECUTION_TIMES=True,
        MAX_RETRIES=2,
    ))

    mcp = MCPBridge(MCP_SERVER)
    tools = await build_agent_tools_from_mcp(mcp)

    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    calc_agent = BedrockLLMAgent(BedrockLLMAgentOptions(
        name="Calc Agent",
        description="Performs math using MCP calculator tools.",
        client=bedrock_client,
        model_id=model_id,
        streaming=False,
        tool_config={
            "tool": tools,
            "toolMaxRecursions": 4,
        },
        custom_system_prompt={"template": system_prompt},
    ))

    orchestrator.add_agent(calc_agent)
    return orchestrator
