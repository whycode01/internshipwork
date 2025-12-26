#!/usr/bin/env python3
"""
Simple Intelligence module without adaptive policy
This provides fast, reliable responses without complex processing
"""

import time
from typing import Optional

from groq import Groq

from intelligence.intelligence import Intelligence
from tts.tts import TTS


class SimpleIntelligence(Intelligence):
    def __init__(self, api_key: str, tts: TTS, model: Optional[str] = None, system_prompt: Optional[str] = None, agent_name: str = "AI Interviewer"):
        print("🔧 [SIMPLE] Initializing Simple Intelligence (No Adaptive Policy)")
        
        self.agent_name = agent_name
        self.tts = tts
        self.model = model or "llama-3.1-8b-instant"
        self.system_prompt = system_prompt or self._get_default_prompt()
        self.chat_history = []
        self.pubsub = None
        
        # Initialize Groq client
        try:
            self.client = Groq(api_key=api_key)
            print("✅ [SIMPLE] Groq client initialized successfully")
        except Exception as e:
            print(f"❌ [SIMPLE] Error initializing Groq: {e}")
            self.client = None

    def _get_default_prompt(self):
        """Get a simple default prompt"""
        return """You are a friendly AI interviewer conducting a technical interview. 
        
Your approach:
- Ask clear, direct questions
- Listen to answers and provide appropriate follow-ups
- Keep the conversation flowing naturally
- Be encouraging and professional
        
Communication rules:
- Use natural, conversational language
- No asterisks (*) or formatting symbols
- No filler words (um, uh, basically, actually)
- Speak directly as if having a natural conversation
        
Start by introducing yourself and begin the interview."""

    def set_pubsub(self, pubsub):
        """Set the pubsub function for meeting chat"""
        self.pubsub = pubsub

    def generate(self, text: str, sender_name: str, is_agent_introduction: bool = False):
        """Generate response - simplified version"""
        print(f"🎯 [SIMPLE] Generating response for: {text[:50]}...")
        start_time = time.time()
        
        try:
            # Handle introduction
            if is_agent_introduction:
                self._handle_introduction(text, sender_name)
                return
                
            # Handle regular conversation
            self._handle_conversation(text, sender_name)
            
        except Exception as e:
            print(f"❌ [SIMPLE] Error: {e}")
            self._handle_fallback(text, sender_name)
        
        elapsed = time.time() - start_time
        print(f"⏱️ [SIMPLE] Response generated in {elapsed:.2f} seconds")

    def _handle_introduction(self, text: str, sender_name: str):
        """Handle agent introduction"""
        print(f"👋 [SIMPLE] Agent introduction")
        
        # Publish to meeting chat
        if self.pubsub:
            self.pubsub(message=f"[{sender_name}]: {text}")
        
        # Send to TTS
        self.tts.generate(text=text)
        
        # Add to history
        self.chat_history.append({
            "role": "assistant",
            "content": text
        })

    def _handle_conversation(self, text: str, sender_name: str):
        """Handle regular conversation"""
        print(f"💬 [SIMPLE] Processing conversation")
        
        if not self.client:
            self._handle_fallback(text, sender_name)
            return
        
        # Build messages
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add recent chat history (last 6 messages to keep context manageable)
        recent_history = self.chat_history[-6:] if len(self.chat_history) > 6 else self.chat_history
        messages.extend(recent_history)
        
        # Add current message
        messages.append({
            "role": "user", 
            "content": f"{sender_name}: {text}"
        })
        
        # Generate response with fast settings
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=512,  # Shorter for faster response
                top_p=0.9,
                stream=False
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Clean response
            cleaned_response = self._clean_response(response_text)
            
            # Send to TTS
            if cleaned_response:
                print(f"🗣️ [SIMPLE] AI Response: {cleaned_response[:100]}...")
                self.tts.generate(text=cleaned_response)
                
                # Publish to meeting chat
                if self.pubsub:
                    self.pubsub(message=f"[{self.agent_name}]: {cleaned_response}")
                
                # Update history
                self.chat_history.append({
                    "role": "user",
                    "content": text
                })
                self.chat_history.append({
                    "role": "assistant", 
                    "content": cleaned_response
                })
                
        except Exception as e:
            print(f"❌ [SIMPLE] Groq API error: {e}")
            self._handle_fallback(text, sender_name)

    def _clean_response(self, response: str) -> str:
        """Clean response for TTS"""
        import re

        # Remove formatting and unwanted characters
        cleaned = re.sub(r'\*+', '', response)  # Remove asterisks
        cleaned = re.sub(r'#{1,6}\s*', '', cleaned)  # Remove markdown headers
        cleaned = re.sub(r'\[.*?\]', '', cleaned)  # Remove brackets
        cleaned = re.sub(r'\(.*?\)', '', cleaned)  # Remove parentheses
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        
        return cleaned.strip()

    def _handle_fallback(self, text: str, sender_name: str):
        """Fallback response when everything else fails"""
        fallback_responses = [
            "That's interesting. Can you tell me more about your approach?",
            "I see. What other aspects of this topic would you like to discuss?", 
            "Good point. How would you handle a different scenario?",
            "Thanks for sharing. Let's explore another question.",
            "I understand. What's your experience with similar challenges?"
        ]
        
        import random
        response = random.choice(fallback_responses)
        
        print(f"🔄 [SIMPLE] Using fallback response: {response}")
        
        # Send to TTS
        self.tts.generate(text=response)
        
        # Publish to meeting chat
        if self.pubsub:
            self.pubsub(message=f"[{self.agent_name}]: {response}")

    def build_messages(self, text: str, sender_name: str = "User"):
        """Build message history for LLM"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add recent history
        recent_history = self.chat_history[-4:] if len(self.chat_history) > 4 else self.chat_history
        messages.extend(recent_history)
        
        # Add current message
        messages.append({
            "role": "user",
            "content": f"{sender_name}: {text}"
        })
        
        return messages
