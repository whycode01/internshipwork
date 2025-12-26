import asyncio
from fastmcp import Client
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Client("http://localhost:8000/mcp")

async def llm_extract_params(user_input: str) -> dict:
    prompt = (
        "Extract the following parameters from the user's input and respond ONLY with a STRICT JSON object containing these keys:\n"
        "- weather_location: Name of the city to get weather for, or null if not mentioned\n"
        "- time_city: Name of the city to get current time for, or null if not mentioned\n"
        "- news_topic: The topic of news requested (e.g. 'cricket', 'technology'), or null if not mentioned\n\n"
        "Rules:\n"
        "- The output MUST be parsable JSON only, no explanations or extra text.\n"
        "- Parse the user input robustly, handling different capitalizations, punctuation, and phrasing.\n"
        "- If multiple weather/time cities mentioned, choose the most relevant or first.\n"
        "- If news requested without topic, return null for news_topic.\n\n"
        f"User input: {user_input}\n"
        "Output JSON:"
    )
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 200,
    }
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
    generated_text = data["choices"][0]["message"]["content"].strip()
    print("LLM Extraction Output:", generated_text)
    try:
        return json.loads(generated_text)
    except json.JSONDecodeError:
        return {"weather_location": None, "time_city": None, "news_topic": None}

async def run():
    user_input = input("Enter your query (e.g. 'time in Tokyo, weather in Paris, top 5 news'): ")

    # Get params from LLM
    params = await llm_extract_params(user_input)
    print(f"Parsed parameters: {params}")

    tasks = []
    async with client:
        # Call weather tool if parameter is present
        weather_loc = params.get("weather_location")
        if weather_loc:
            tasks.append(client.call_tool("get_weather_tool", {"location": weather_loc}))

        # Call time tool if parameter is present
        time_city = params.get("time_city")
        if time_city:
            tasks.append(client.call_tool("get_time_tool", {"city": time_city}))

        # Call news tool if parameter present or default to general
        news_topic = params.get("news_topic") or "general"
        tasks.append(client.call_tool("get_news_tool", {"topic": news_topic, "count": 5}))

        results = await asyncio.gather(*tasks)

    print("\n=== Combined Agent Response ===")
    for res in results:
        print(res.data)

if __name__ == "__main__":
    asyncio.run(run())
