from typing import Optional

from agent_squad.agents import Agent, AgentOptions
from agent_squad.types import ConversationMessage, ParticipantRole

from entity_extractor import GroqEntityExtractor  # you'll create this file


class MetaAgent(Agent):
    def __init__(self, weather_agent, time_agent, news_agent):
        options = AgentOptions(name="MetaAgent", description="LLM-routed meta agent.")
        super().__init__(options)
        self.weather_agent = weather_agent
        self.time_agent = time_agent
        self.news_agent = news_agent
        self.extractor = GroqEntityExtractor()

    async def process_request(self, input_text: str, user_id: str, session_id: str,
                              chat_history: list[ConversationMessage],
                              additional_params: Optional[dict] = None) -> ConversationMessage:
        messages = []
        extracted = self.extractor.extract_entities(input_text)

        # Route to WeatherAgent
        weather_loc = extracted.get("weather_location")
        if weather_loc:
            weather_input = f"weather in {weather_loc}"
            resp = await self.weather_agent.process_request(weather_input, user_id, session_id, chat_history)
            messages.append(f"🌤 WeatherAgent:\n{resp.content[0]['text']}")

        # Route to TimeAgent
        time_loc = extracted.get("time_location")
        if time_loc:
            time_input = f"time in {time_loc}"
            resp = await self.time_agent.process_request(time_input, user_id, session_id, chat_history)
            messages.append(f"⏰ TimeAgent:\n{resp.content[0]['text']}")

        # Route to NewsAgent
        if extracted.get("news_requested"):
            resp = await self.news_agent.process_request("news", user_id, session_id, chat_history)
            messages.append(f"{resp.content[0]['text']}")

        if not messages:
            messages.append("No relevant information found in your request.")

        return ConversationMessage(role=ParticipantRole.ASSISTANT, content=[{"text": "\n\n".join(messages)}])
