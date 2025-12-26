import os
from typing import Any, List

import requests
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage


class GroqChat(BaseChatModel):
    model: str = "llama3-70b-8192"
    temperature: float = 0.3
    groq_api_key: str = os.getenv("GROQ_API_KEY")

    def _llm_type(self) -> str:
        return "groq"

    def _stream(self, messages: List[HumanMessage], **kwargs: Any):
        history = [{"role": m.type, "content": m.content} for m in messages]

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": history,
                "temperature": self.temperature,
                "stream": False
            }
        )
        content = response.json()["choices"][0]["message"]["content"]
        yield AIMessage(content=content)
