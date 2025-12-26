import os

from langchain_mcp_adapters.client import MultiServerMCPClient


def get_mcp_config():
    return {
        "github": {
            "url": "https://api.githubcopilot.com/mcp/",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {os.getenv('GITHUB_PAT')}"
            }
        }
    }

async def load_tools():
    client = MultiServerMCPClient(get_mcp_config())
    tools = await client.get_tools()

    print("\n🔧 Available tools (filtered preview):")
    for t in tools:
        if "commit" in t.name or "pull" in t.name:
            print(f"- {t.name}")
    return tools
