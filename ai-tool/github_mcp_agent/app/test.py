import asyncio
import os

from dotenv import load_dotenv

from app.mcp_client import load_tools

load_dotenv()

async def main():
    print("🔄 Loading GitHub MCP tools...")
    tools = await load_tools()
    tool_map = {t.name: t for t in tools}

    # ✅ Pick just the one we want
    tool = tool_map.get("search_repositories")
    if not tool:
        print("❌ Tool 'search_repositories' not found")
        return

    # ✅ Provide your GitHub username here
    github_username = "whycode01"
    query = f"user:{github_username}"

    print(f"\n🔍 Searching repositories for: {query}")
    result = await tool.ainvoke({"query": query})

    print("\n✅ Found repositories:")
    if isinstance(result, list):
        for i, repo in enumerate(result, 1):
            print(f"{i}. {repo.get('full_name')}")
    else:
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
