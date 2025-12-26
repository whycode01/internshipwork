import os

from langchain.agents import create_react_agent
from langchain.agents.agent import RunnableAgent
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_groq import ChatGroq


def build_agent(tools: list[Tool]) -> RunnableAgent:
    """
    Builds a ReAct agent using the provided tools.
    The tool filtering logic has been removed from this function, 
    as it's now handled in app.py before this function is called.
    """
    
    # <<< CHANGE: Updated the model to kimi-k2-instruct and adjusted temperature >>>
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="moonshotai/kimi-k2-instruct",
        temperature=0.6  # Using the temperature from your example
    )

    # The robust prompt works well for multiple models.
    prompt = PromptTemplate.from_template(
        """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: a valid JSON object with keys that match the tool's argument names.
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
{agent_scratchpad}"""
    )

    # <<< CHANGE: The agent is now created with the tools passed directly into the function >>>
    # This makes the build_agent function more generic and reusable.
    return create_react_agent(llm=llm, tools=tools, prompt=prompt)