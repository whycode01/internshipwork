import os
from agent_squad.types import ConversationMessage
from agent_squad.agents import Agent, AgentOptions
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LlamaGroqAgent(Agent):
    def __init__(self, options: AgentOptions):
        super().__init__(options)
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def process_request(self, input_text, user_id, session_id, chat_history, additional_params=None):
        messages = [{"role": "user", "content": input_text}]
        response = self.client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
        )
        answer = response.choices[0].message.content
        return ConversationMessage(role="assistant", content=[{"text": answer}])
