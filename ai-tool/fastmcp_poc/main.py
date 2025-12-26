from fastmcp import FastMCP
from tools import WeatherTool, TimeTool, NewsTool
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.7,
    groq_api_key=GROQ_API_KEY
)

mcp = FastMCP("LangChain + FastMCP + Groq LLaMA Server")

weather_tool = WeatherTool()
time_tool = TimeTool()
news_tool = NewsTool()

@mcp.tool()
def get_weather_tool(location: str) -> str:
    return weather_tool._run(location)

@mcp.tool()
def get_time_tool(city: str) -> str:
    return time_tool._run(city)

@mcp.tool()
def get_news_tool(topic: str = "general", count: int = 5) -> str:
    return news_tool._run(topic, count)

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
