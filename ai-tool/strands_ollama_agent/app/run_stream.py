import asyncio
from strands import Agent
from strands.models.ollama import OllamaModel
from strands_tools import calculator

ollama_model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.2:3b",
    temperature=0.3,
)

agent = Agent(model=ollama_model, tools=[calculator], callback_handler=None)

async def main():
    async for event in agent.stream_async("Explain sqrt(144) and then add 7 using tools."):
        if event.get("delta"):
            print(event["delta"], end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
