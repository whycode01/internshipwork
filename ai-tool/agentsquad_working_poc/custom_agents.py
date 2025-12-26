import datetime
import os
import re
import json
import pytz
import requests
from agent_squad.agents import Agent, AgentOptions
from agent_squad.types import ConversationMessage, ParticipantRole
from dotenv import load_dotenv
from newsapi import NewsApiClient

load_dotenv()

with open('timezones.json') as f:
    timezones = json.load(f)

tz_map = timezones

class WeatherAgent(Agent):
    def __init__(self):
        api_key = os.getenv("OPENWEATHER_API_KEY")
        options = AgentOptions(name="WeatherAgent", description="Provides weather info")
        super().__init__(options)
        self.api_key = api_key

    async def process_request(self, input_text, user_id, session_id, chat_history, additional_params=None):
        location = self._extract_location(input_text)
        if not location:
            return ConversationMessage(role=ParticipantRole.ASSISTANT, content=[{"text": "I couldn't find a location in your weather query."}])

        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": location, "appid": self.api_key, "units": "metric"}
        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if data.get("cod") == 200:
                temp = round(data["main"]["temp"])
                desc = data["weather"][0]["description"]
                content = f"The current temperature in {location} is {temp}°C with {desc}."
            else:
                content = f"Weather data not found for {location}."
        except Exception as e:
            content = f"Weather service error: {e}"

        return ConversationMessage(role=ParticipantRole.ASSISTANT, content=[{"text": content}])

    def _extract_location(self, text: str) -> str | None:
        match = re.search(r"weather in ([a-zA-Z\s]+)", text, re.IGNORECASE)
        return match.group(1).strip().title() if match else None


class TimeAgent(Agent):
    def __init__(self):
        options = AgentOptions(name="TimeAgent", description="Provides time info")
        super().__init__(options)

    async def process_request(self, input_text, user_id, session_id, chat_history, additional_params=None):
        location = self._extract_location(input_text)
        if not location or location not in tz_map:
            return ConversationMessage(role=ParticipantRole.ASSISTANT, content=[{"text": f"Sorry, I don't know the timezone for '{location or 'unknown'}'."}])

        try:
            now = datetime.datetime.now(pytz.timezone(tz_map[location]))
            return ConversationMessage(role=ParticipantRole.ASSISTANT, content=[{"text": f"The current time in {location} is {now.strftime('%H:%M:%S')}."}])
        except Exception as e:
            return ConversationMessage(role=ParticipantRole.ASSISTANT, content=[{"text": f"Time service error: {e}"}])

    def _extract_location(self, text: str) -> str | None:
        match = re.search(r"time in ([a-zA-Z\s]+)", text, re.IGNORECASE)
        return match.group(1).strip().title() if match else None


class NewsAgent(Agent):
    def __init__(self):
        api_key = os.getenv("NEWS_API_KEY")
        options = AgentOptions(name="NewsAgent", description="Provides top global news headlines.")
        super().__init__(options)
        self.client = NewsApiClient(api_key=api_key)

    async def process_request(self, input_text, user_id, session_id, chat_history, additional_params=None):
        try:
            response = self.client.get_top_headlines(
                sources='bbc-news,the-verge',
                language='en',
                page_size=5
            )
            articles = response.get("articles", [])
            if not articles:
                return ConversationMessage(
                    role=ParticipantRole.ASSISTANT,
                    content=[{"text": "No top news available right now."}]
                )

            lines = [f"{i+1}. {a['title']} ({a['source']['name']})" for i, a in enumerate(articles)]
            return ConversationMessage(
                role=ParticipantRole.ASSISTANT,
                content=[{"text": "📰 Top News Headlines:\n" + "\n".join(lines)}]
            )

        except Exception as e:
            return ConversationMessage(
                role=ParticipantRole.ASSISTANT,
                content=[{"text": f"News service error: {e}"}]
            )
