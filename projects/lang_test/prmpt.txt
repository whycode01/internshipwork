import operator
from datetime import datetime
from typing import Annotated, Literal, TypedDict

import pytz
from dotenv import load_dotenv
from langchain.tools import StructuredTool
from langchain_core.messages import (AIMessage, AnyMessage, HumanMessage,
                                     SystemMessage)
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

load_dotenv()

# ---------------- Tools ----------------
search_tool = TavilySearch(max_results=2, include_answer=True)

def calculator(expression: str) -> str:
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"Error: {e}"

calculator_tool = StructuredTool.from_function(
    func=calculator,
    name="calculator", 
    description="Evaluate math expressions like '2+2' or '25*30+100'"
)

def time_in_region(region: str) -> str:
    try:
        tz = pytz.timezone(region)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e:
        return f"Error: {e}"

time_tool = StructuredTool.from_function(
    func=time_in_region,
    name="time_in_region",
    description="Get current time in timezone like 'America/New_York' or 'Asia/Kolkata'"
)

tools = [search_tool, calculator_tool, time_tool]

# ---------------- State ----------------
class State(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# ---------------- Nodes ----------------
def chatbot(state: State):
    """ReAct agent with Chain of Thought reasoning"""

    # Enhanced ReAct Chain of Thought system prompt
    react_prompt = """You are a ReAct (Reasoning + Acting) agent that uses Chain of Thought reasoning.

AVAILABLE TOOLS:
- tavily_search: Search the web for current information, news, facts, events
- calculator: Perform mathematical calculations and evaluate expressions
- time_in_region: Get current time in specific timezones

REACT REASONING PROCESS:
Follow this step-by-step reasoning pattern:

1. THOUGHT: Analyze the user's question/request
   - What exactly is the user asking?
   - What type of information do I need to provide a complete answer?

2. REASONING: Determine the approach
   - Do I need current/real-time information? → Use tavily_search
   - Do I need to perform calculations? → Use calculator
   - Do I need timezone/time information? → Use time_in_region
   - Can I answer directly from my knowledge? → Provide direct response

3. ACTION: If a tool is needed, explain which tool and why
   - Which specific tool will help answer this question?
   - What exact parameters should I use?
   - What information am I trying to obtain?

4. OBSERVATION: After tool use (if applicable)
   - Analyze the results from the tool
   - Determine if I have enough information to answer
   - Decide if additional tools are needed

5. FINAL ANSWER: Synthesize the information
   - Provide a comprehensive response based on reasoning and observations
   - Ensure the answer directly addresses the user's question

IMPORTANT:
- Always show your reasoning process step by step
- Be explicit about why you're choosing specific tools
- If you don't need tools, explain your reasoning for direct response
- Use tools when you need current information, calculations, or specific data

Example reasoning format:
THOUGHT: The user is asking about [analysis of question]
REASONING: I need to [explain what type of information is needed]
ACTION: I will use [tool name] because [explanation of why this tool is appropriate]
"""

    model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0).bind_tools(tools)

    # Add the ReAct system prompt
    messages_with_system = [SystemMessage(content=react_prompt)] + state["messages"]

    response = model.invoke(messages_with_system)
    return {"messages": [response]}

def route_after_chatbot(state: State) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"

# ---------------- Graph ----------------
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools))

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", route_after_chatbot)
graph_builder.add_edge("tools", "chatbot")

# Compile WITHOUT checkpointer for LangGraph Studio
# The platform handles persistence automatically
graph = graph_builder.compile(
    interrupt_before=["tools"]  # Human-in-the-loop before tool execution
)

# Export the graph for LangGraph Studio
__all__ = ["graph"]
