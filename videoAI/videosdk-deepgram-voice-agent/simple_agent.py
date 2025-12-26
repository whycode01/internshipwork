#!/usr/bin/env python3
"""
Emergency fix: Simplified AI agent without adaptive policy
Use this when the main agent gets stuck or has delays
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple configuration
ROOM_ID = os.getenv("ROOM_ID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN") 
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LANGUAGE = os.getenv("LANGUAGE", "en-US")

def create_simple_agent():
    """Create a simplified agent without adaptive policy"""
    
    print("🚀 Starting Simple AI Agent (No Adaptive Policy)")
    print("=" * 50)
    print("This version bypasses adaptive policy for faster responses")
    print()
    
    # Import after we know we need them
    from agent.agent import AIInterviewer
    from agent.audio_stream_track import CustomAudioStreamTrack
    # Create a simplified intelligence client
    from intelligence.simple_intelligence import SimpleIntelligence
    from stt.deepgram_stt import DeepgramSTT
    from tts.deepgram_tts import DeepgramTTS
    
    print("✅ All imports successful")
    return "Simple agent ready to create"

def main():
    """Main function for simple agent"""
    print("🔧 Emergency Simple AI Agent")
    print("=" * 30)
    print("Use this when the main agent gets stuck")
    print()
    print("To run the simple agent:")
    print("1. First, let me create a simplified intelligence module")
    print("2. Then run: python simple_agent.py")
    print()
    print("This bypasses the adaptive policy that might be causing delays")

if __name__ == "__main__":
    main()
