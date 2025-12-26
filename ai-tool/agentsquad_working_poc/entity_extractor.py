import json
import os

from groq import Groq


class GroqEntityExtractor:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def extract_entities(self, query: str) -> dict:
        prompt = f"""
You are an assistant that extracts structured entities from user queries.

For the given user query, extract:
- weather_location: city name if weather is mentioned
- time_location: city name if time is mentioned
- news_requested: true if the user asked for news or headlines

Respond with only a JSON object. No explanations.

Example format:
{{
  "weather_location": "London",
  "time_location": "New York",
  "news_requested": true
}}

User query:
"{query}"
"""

        response = self.client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content.strip()
        print("\n🧠 LLM Raw Output:\n", content)  # Debug output

        try:
            return json.loads(content)
        except Exception as e:
            print("⚠️ Failed to parse JSON:", e)
            return {
                "weather_location": None,
                "time_location": None,
                "news_requested": False
            }
