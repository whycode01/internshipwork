import asyncio
import json
import traceback

from dotenv import load_dotenv
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import Tool

from app.langgraph_agent import build_agent
from app.mcp_client import load_tools

load_dotenv()

async def main():
    print("🔄 Loading GitHub MCP tools...")
    tools = await load_tools()
    tool_map = {tool.name: tool for tool in tools}
    print(f"✅ Loaded {len(tools)} tools")

    agent = build_agent(tools)
    print("🤖 Agent ready. Type a query or 'exit':")

    while True:
        user_input = input("\nYou > ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Exiting.")
            break

        try:
            steps = []
            inputs = {"input": user_input, "intermediate_steps": steps}

            while True:
                output = await agent.ainvoke(inputs)

                if isinstance(output, AgentFinish):
                    print("\n✅ Final Answer:\n", output.return_values["output"])
                    break

                elif isinstance(output, AgentAction):
                    print(f"\n🛠 Tool selected: {output.tool}")
                    tool = tool_map.get(output.tool)
                    if tool is None:
                        raise ValueError(f"Tool '{output.tool}' not found in available tools.")

                    # Parse tool input safely
                    tool_input_raw = output.tool_input
                    if isinstance(tool_input_raw, dict):
                        parsed_input = tool_input_raw
                    elif isinstance(tool_input_raw, str):
                        try:
                            parsed_input = json.loads(tool_input_raw)
                        except json.JSONDecodeError:
                            # fallback if it's a plain string, not JSON
                            parsed_input = {"input": tool_input_raw}
                    else:
                        parsed_input = {"input": str(tool_input_raw)}

                    # Call the tool and update steps
                    observation = await tool.ainvoke(parsed_input)
                    print(f"\n📎 Observation: {observation}")
                    steps.append((output, observation))
                    inputs["intermediate_steps"] = steps

                else:
                    print("\n⚠️ Unexpected agent output:", output)
                    break

        except Exception as e:
            print("\n❌ Error during agent execution:")
            traceback.print_exc()
            print(f"\n🔍 Hint: If the issue is 'OutputParserException', make sure the LLM response format matches ReAct expectations.")

if __name__ == "__main__":
    asyncio.run(main())
