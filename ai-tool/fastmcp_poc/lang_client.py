import asyncio
import json
import re
from fastmcp import Client
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = "http://localhost:8000/mcp"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)

async def parse_user_input_to_tools(llm, user_input: str) -> dict:
    prompt = f"""
You will be given a single user input query.
Identify if the user wants current weather, local time, and/or news.
If mentioned, extract parameters such as city (for weather/time) and topic (for news).
Respond ONLY in JSON format showing the detected tools and their parameters.

Example output format:
{{
  "weather": {{"location": "Paris"}},
  "time": {{"city": "Tokyo"}},
  "news": {{"topic": "technology"}}
}}

If a tool is not requested, omit its key.
User input: \"\"\"{user_input}\"\"\"
"""
    response = await llm.ainvoke(prompt)
    text = response.content  # <-- Use .content, not .data
    print("Raw model output:", text)  # Debug print to see output

    try:
        return json.loads(text)
    except:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except Exception as e:
                print("JSON extraction failed:", e)
        print("JSON parsing error. Returning empty dict.")
        return {}

async def main():
    async with Client(SERVER_URL) as client:
        await client.ping()
        print("Connected to MCP server.")

        while True:
            user_input = input("\nEnter your question (or 'exit' to quit): ").strip()
            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            tools_to_call = await parse_user_input_to_tools(llm, user_input)

            if not tools_to_call:
                print("Sorry, I couldn't understand what tools to call.")
                continue

            tasks = []

            if "weather" in tools_to_call:
                location = tools_to_call["weather"].get("location", "unknown")
                tasks.append(client.call_tool("get_weather_tool", {"location": location}))

            if "time" in tools_to_call:
                city = tools_to_call["time"].get("city", "unknown")
                tasks.append(client.call_tool("get_time_tool", {"city": city}))

            if "news" in tools_to_call:
                topic = tools_to_call["news"].get("topic", "general")
                tasks.append(client.call_tool("get_news_tool", {"topic": topic, "count": 5}))

            if not tasks:
                print("Could not detect any known tool to call, please ask about weather, time, or news.")
                continue

            results = await asyncio.gather(*tasks)

            for result in results:
                if hasattr(result, "data"):
                    print(result.data)
                else:
                    print(result)

if __name__ == "__main__":
    asyncio.run(main())
