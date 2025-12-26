import os

os.environ['GROQ_API_KEY'] = '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'

from intelligence.groq_intelligence import GroqIntelligence
from tts.tts import TTS


class MockTTS(TTS):
    def __init__(self):
        pass
        
    def generate(self, text): 
        print(f'🔊 TTS: "{text}"')

class MockPubSub:
    def __init__(self):
        self.messages = []
        
    def __call__(self, message):
        self.messages.append(message)
        print(f'💬 CHAT: {message}')

try:
    print("🧪 Testing TTS formatting and follow-up handling...")
    
    # Create mock pubsub
    pubsub = MockPubSub()
    
    # Create intelligence client
    intelligence = GroqIntelligence('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', MockTTS())
    
    # Set pubsub
    intelligence.set_pubsub(pubsub)
    
    print(f'✅ GroqIntelligence created (fallback: {intelligence.using_fallback_client})')
    
    # Test 1: Response with formatting symbols
    print('\n🎯 Test 1: Formatting cleanup...')
    test_response = "**Question:** What does NLP stand for? **Type:** Concept **Topic:** Applications"
    cleaned = intelligence._clean_response_for_tts(test_response)
    print(f'Original: "{test_response}"')
    print(f'Cleaned:  "{cleaned}"')
    
    # Test 2: Follow-up handling
    print('\n🎯 Test 2: Follow-up conversation...')
    intelligence.generate("NLP stands for natural language processing", "TestUser")
    
    print('\n🎯 Test 3: Edge case question...')
    intelligence.generate("What edge cases should I consider?", "TestUser")
    
    print('\n🎯 Test 4: Next question request...')
    intelligence.generate("Next", "TestUser")
    
    print('\n✅ All tests completed!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
