import os
import tempfile
import soundfile as sf
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import groq, silero
from elevenlabs import ElevenLabs, VoiceSettings

# Load environment variables
load_dotenv(dotenv_path=".env")

# --- Capabilities Helper ---
class Capabilities:
    def __init__(self, streaming=False):
        self.streaming = streaming

# --- ElevenLabs TTS Wrapper ---
class ElevenLabsTTS:
    def __init__(self, voice="Rachel"):
        self.voice = voice
        self.client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

    @property
    def sample_rate(self) -> int:
        return 22050

    @property
    def num_channels(self) -> int:
        return 1

    @property
    def capabilities(self):
        return Capabilities(streaming=False)

    def on(self, event_name: str):
        def noop(*args, **kwargs):
            pass
        return noop

    async def generate(self, text: str):
        audio_bytes = self.client.generate(
            text=text,
            voice=self.voice,
            model="eleven_monolingual_v1",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        data, samplerate = sf.read(tmp_path)
        return data, samplerate

# --- Manual NonStreamingAdapter ---
class NonStreamingAdapter:
    def __init__(self, tts):
        self._tts = tts
        self.sample_rate = tts.sample_rate
        self.num_channels = tts.num_channels
        self.capabilities = Capabilities(streaming=False)

    def on(self, event_name: str):
        return self._tts.on(event_name)

    async def synthesize(self, text: str):
        data, _ = await self._tts.generate(text)
        yield type("AudioFrame", (), {"frame": data})()  # minimal AudioFrame-like object

# --- Example Tool ---
@function_tool
async def lookup_weather(context: RunContext, location: str):
    """Used to look up weather information."""
    return {"weather": "sunny", "temperature": 70}

# --- Main Entrypoint ---
async def entrypoint(ctx: JobContext):
    await ctx.connect()

    agent = Agent(
        instructions="""
        You are a friendly voice assistant built by LiveKit.
        Start every conversation by greeting the user.
        Only use the `lookup_weather` tool if the user specifically asks for weather information.
        Never assume a location or provide weather data without a request.
        """,
        tools=[lookup_weather],
    )

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=groq.STT(),
        llm=groq.LLM(model="llama3-70b-8192"),
        tts=NonStreamingAdapter(ElevenLabsTTS()),
    )

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions="Say hello, then ask how the user's day is going and how you can help.")

# --- CLI Entrypoint ---
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
