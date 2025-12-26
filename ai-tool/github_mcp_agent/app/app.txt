import asyncio
import json
import traceback

from dotenv import load_dotenv
from langchain_core.agents import AgentAction, AgentFinish

from app.langgraph_agent import build_agent
from app.mcp_client import load_tools

load_dotenv()

async def main():
    print("🔄 Loading all 81 GitHub MCP tools...")
    all_tools = await load_tools()
    tool_map = {tool.name: tool for tool in all_tools}
    print(f"✅ Loaded {len(all_tools)} total tools.")

    # This is now the single source of truth for which tools the agent will use.
    selected_tool_names = {
        "search_repositories",
        "list_commits",
        "get_pull_request",
        "list_pull_requests",
        "get_pull_request_files",
    }
    
    filtered_tools = [t for t in all_tools if t.name in selected_tool_names]
    
    if not filtered_tools:
        print("❌ Error: None of the selected tools were found. Exiting.")
        return
        
    print(f"\n🤖 Building agent with {len(filtered_tools)} filtered tools: {', '.join(t.name for t in filtered_tools)}")

    # The filtered list is passed to our updated build_agent function.
    agent = build_agent(filtered_tools)
    
    print("✅ Agent ready. Type a query or 'exit':")

    while True:
        user_input = input("\nYou > ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Exiting.")
            break

        try:
            steps = []
            inputs = {"input": user_input, "intermediate_steps": steps}

            for _ in range(5): 
                output = await agent.ainvoke(inputs)

                if isinstance(output, AgentFinish):
                    print("\n✅ Final Answer:\n", output.return_values["output"])
                    break

                if isinstance(output, AgentAction):
                    print(f"\n🤔 Thought: {output.log.strip()}")
                    print(f"🛠️ Action: {output.tool}")
                    print(f"📥 Action Input Text: {output.tool_input}")
                    
                    tool_to_use = tool_map.get(output.tool)
                    if not tool_to_use:
                        observation = f"Error: Tool '{output.tool}' not found."
                    else:
                        tool_input_str = output.tool_input
                        parsed_input = {}
                        if isinstance(tool_input_str, dict):
                            parsed_input = tool_input_str
                        elif isinstance(tool_input_str, str):
                            try:
                                parsed_input = json.loads(tool_input_str)
                            except json.JSONDecodeError:
                                observation = f"Error: The tool input was not valid JSON: {tool_input_str}"
                                parsed_input = None
                        
                        if parsed_input is not None:
                            observation = await tool_to_use.ainvoke(parsed_input)

                    print(f"\n👀 Observation: {observation}")
                    steps.append((output, str(observation))) 
                    inputs["intermediate_steps"] = steps
                else:
                    print(f"\n⚠️ Unexpected agent output type: {type(output)}")
                    break
            else:
                print("\n⚠️ Agent reached maximum steps. Finishing.")

        except Exception as e:
            print("\n❌ Error during agent execution:")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())