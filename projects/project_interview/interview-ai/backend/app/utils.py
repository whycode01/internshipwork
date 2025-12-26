import os
import json

def get_deepgram_api_key():
    # Grabs the Deepgram key from environment or defaults to provided one
    return os.getenv("DEEPGRAM_API_KEY", "d572934eb60cf3e1409706878b34faf7a92dcc6d")

def extract_transcript(deepgram_message: str) -> str:
    try:
        data = json.loads(deepgram_message)
        alternatives = data.get("channel", {}).get("alternatives", [])
        if alternatives and "transcript" in alternatives[0]:
            return alternatives[0]["transcript"]
        return ""
    except Exception as e:
        print(f"[ERROR] Failed to parse Deepgram message: {e}")
        return ""
