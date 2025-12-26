import pytest
import asyncio
from unittest.mock import patch

from custom_agents import WeatherAgent, TimeAgent, NewsAgent
from meta_agent import MetaAgent
from agent_squad.types import ConversationMessage, ParticipantRole


@pytest.mark.asyncio
async def test_weather_agent():
    agent = WeatherAgent()
    result = await agent.process_request("what's the weather in Tokyo", "user", "session", [])
    assert isinstance(result, ConversationMessage)
    assert result.role == ParticipantRole.ASSISTANT
    assert "Tokyo" in result.content[0]["text"] or "Weather service error" in result.content[0]["text"]


@pytest.mark.asyncio
async def test_time_agent():
    agent = TimeAgent()
    result = await agent.process_request("what's the time in London", "user", "session", [])
    assert isinstance(result, ConversationMessage)
    assert result.role == ParticipantRole.ASSISTANT
    assert "London" in result.content[0]["text"] or "timezone" in result.content[0]["text"]


@pytest.mark.asyncio
async def test_news_agent():
    agent = NewsAgent()
    result = await agent.process_request("give me the news", "user", "session", [])
    assert isinstance(result, ConversationMessage)
    assert result.role == ParticipantRole.ASSISTANT
    assert "news" in result.content[0]["text"].lower() or "No top news" in result.content[0]["text"]


@pytest.mark.asyncio
@patch("entity_extractor.GroqEntityExtractor.extract_entities")
async def test_meta_agent_routes_all(mock_extract):
    # Simulate Groq output
    mock_extract.return_value = {
        "weather_location": "Tokyo",
        "time_location": "Paris",
        "news_requested": True
    }

    weather = WeatherAgent()
    time = TimeAgent()
    news = NewsAgent()
    meta = MetaAgent(weather, time, news)

    result = await meta.process_request("what's the weather in Tokyo, time in Paris, and news", "user", "session", [])

    assert isinstance(result, ConversationMessage)
    output = result.content[0]["text"]
    assert "WeatherAgent" in output
    assert "TimeAgent" in output
    assert "news" in output.lower() or "No top news" in output


@pytest.mark.asyncio
@patch("entity_extractor.GroqEntityExtractor.extract_entities")
async def test_meta_agent_empty(mock_extract):
    mock_extract.return_value = {
        "weather_location": None,
        "time_location": None,
        "news_requested": False
    }

    meta = MetaAgent(WeatherAgent(), TimeAgent(), NewsAgent())
    result = await meta.process_request("hello", "user", "session", [])
    assert "No relevant" in result.content[0]["text"]
