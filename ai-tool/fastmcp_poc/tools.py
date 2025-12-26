import os
import json
import requests
import pytz
import datetime
from langchain.tools import BaseTool
from newsapi import NewsApiClient
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

with open("timezones.json", "r", encoding="utf-8") as f:
    TIMEZONE_MAP = json.load(f)

news_client = NewsApiClient(api_key=NEWS_API_KEY) if NEWS_API_KEY else None

class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = "Get current weather for a city"

    def _run(self, location: str) -> str:
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

    async def _arun(self, location: str) -> str:
        return self._run(location)

class TimeTool(BaseTool):
    name: str = "get_time"
    description: str = "Get local time for a city"

    def _run(self, city: str) -> str:
        tz_name = TIMEZONE_MAP.get(city) or TIMEZONE_MAP.get(city.title())
        if not tz_name:
            return f"Sorry, I don't have timezone information for '{city}'."
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.datetime.now(tz)
            return f"The current time in {city} is {now.strftime('%H:%M:%S')}."
        except Exception as e:
            return f"Time service error: {e}"

    async def _arun(self, city: str) -> str:
        return self._run(city)

class NewsTool(BaseTool):
    name: str = "get_news"
    description: str = "Get top headlines for a topic"

    def _run(self, topic: str = "general", count: int = 5) -> str:
        if not NEWS_API_KEY:
            return "News API key not configured."
        try:
            response = news_client.get_top_headlines(q=topic, language="en", page_size=count)
            articles = response.get("articles", [])
            if not articles:
                response = news_client.get_top_headlines(language="en", page_size=count)
                articles = response.get("articles", [])
            if not articles:
                return f"No recent news found about '{topic}'."
            result_lines = []
            for i, article in enumerate(articles):
                title = article.get("title", "No Title")
                source = article.get("source", {}).get("name", "Unknown")
                url = article.get("url", "")
                line = f"{i+1}. {title} ({source})\n   {url}" if url else f"{i+1}. {title} ({source})"
                result_lines.append(line)
            return f"Top {count} news headlines for '{topic}':\n" + "\n".join(result_lines)
        except Exception as e:
            return f"News service error: {e}"

    async def _arun(self, topic: str = "general", count: int = 5) -> str:
        return self._run(topic, count)
