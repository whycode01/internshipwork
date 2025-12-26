import asyncio

from agent_squad.orchestrator import AgentSquad
from dotenv import load_dotenv

from custom_agents import NewsAgent, TimeAgent, WeatherAgent
from meta_agent import MetaAgent
from orchestrator_config import get_config
from simple_classifier import MetaClassifier

load_dotenv()

async def main():
    weather_agent = WeatherAgent()
    time_agent = TimeAgent()
    news_agent = NewsAgent()

    meta_agent = MetaAgent(weather_agent, time_agent, news_agent)
    classifier = MetaClassifier(meta_agent)

    squad = AgentSquad(
        options=get_config(),
        classifier=classifier,
        default_agent=meta_agent
    )

    squad.add_agent(meta_agent)

    # 🌟 Dynamic input loop
    print("🧠 Type your question below (type 'exit' to quit):\n")
    while True:
        user_input = input("💬 You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        user_id = "user-001"
        session_id = "session-001"

        response = await squad.route_request(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id
        )

        print("\n🤖 Assistant:\n", response.output.content[0]["text"], "\n")

if __name__ == "__main__":
    asyncio.run(main())
