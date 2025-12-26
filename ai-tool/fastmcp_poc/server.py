import os
import datetime
import pytz
import requests
import json
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read API keys from environment
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Load city-to-timezone mapping from a JSON file
with open("timezones.json", "r", encoding="utf-8") as f:
    TIMEZONE_MAP = json.load(f)

# Initialize the FastMCP server instance
mcp = FastMCP("Dynamic MultiAgent MCP Server")

# -----------------------------------------------
# Tool 1: Get Current Weather for a City
# -----------------------------------------------
@mcp.tool()
def get_weather_tool(location: str) -> str:
    """
    Returns the current weather conditions for the given city.
    
    Args:
        location (str): Name of the city (e.g., "Paris").
    
    Returns:
        str: A description of the current temperature and weather, or an error message.
    """
    if not OPENWEATHER_API_KEY:
        return "OpenWeather API key not configured."
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get("cod") == 200:
            temp = round(data["main"]["temp"])
            desc = data["weather"][0]["description"]
            return f"The current temperature in {location} is {temp}°C with {desc}."
        else:
            return f"Weather data not found for {location}."
    except Exception as e:
        return f"Weather service error: {e}"

# -----------------------------------------------
# Tool 2: Get Current Local Time for a City
# -----------------------------------------------
@mcp.tool()
def get_time_tool(city: str) -> str:
    """
    Returns the current local time for the specified city using its timezone.

    Args:
        city (str): Name of the city (e.g., "Tokyo").

    Returns:
        str: A string representing the current local time, or an error message.
    """
    # Look up the city's timezone using the TIMEZONE_MAP
    tz_name = TIMEZONE_MAP.get(city) or TIMEZONE_MAP.get(city.title())
    if not tz_name:
        return f"Sorry, I don't have timezone information for '{city}'."
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.datetime.now(tz)
        return f"The current time in {city} is {now.strftime('%H:%M:%S')}."
    except Exception as e:
        return f"Time service error: {e}"

# -----------------------------------------------
# Tool 3: Get Top Headlines for a News Topic
# -----------------------------------------------
@mcp.tool()
def get_news_tool(topic: str = "general", count: int = 5) -> str:
    """
    Returns the top news headlines for a specified topic.

    Args:
        topic (str): News topic keyword, such as "technology", "cricket", etc. Defaults to "general".
        count (int): Number of headlines to return. Defaults to 5.

    Returns:
        str: List of the top news headlines, or an error message.
    """
    if not NEWS_API_KEY:
        return "News API key not configured."
    try:
        from newsapi import NewsApiClient
    except ImportError:
        return "newsapi package not installed. Install via 'pip install newsapi-python'"
    client = NewsApiClient(api_key=NEWS_API_KEY)
    try:
        response = client.get_top_headlines(
            q=topic,
            language="en",
            page_size=count,
        )
        articles = response.get("articles", [])
        if not articles:
            # fallback to general headlines if no articles found for topic
            response = client.get_top_headlines(language="en", page_size=count)
            articles = response.get("articles", [])
        if not articles:
            return f"No recent news found about '{topic}'."
        result_lines = []
        for i, article in enumerate(articles):
            title = article.get("title", "No Title")
            source = article.get("source", {}).get("name", "Unknown source")
            url = article.get("url", "")
            line = f"{i+1}. {title} ({source})\n   {url}" if url else f"{i+1}. {title} ({source})"
            result_lines.append(line)
        return f"Top {count} news headlines for '{topic}':\n" + "\n".join(result_lines)
    except Exception as e:
        return f"News service error: {e}"

# -----------------------------------------------
# Start the MCP server when run as the main module
# -----------------------------------------------
if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
