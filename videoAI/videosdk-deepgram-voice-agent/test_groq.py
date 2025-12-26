import os

os.environ['GROQ_API_KEY'] = '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'

print("Starting test...")

from intelligence.groq_intelligence import GroqIntelligence
from tts.tts import TTS


class MockTTS(TTS):
    def __init__(self):
        # Implement the abstract __init__ method
        pass
        
    def generate(self, text): 
        print(f'TTS: {text}')

try:
    print("Creating GroqIntelligence instance...")
    intelligence = GroqIntelligence('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', MockTTS())
    print('✅ GroqIntelligence created successfully')
    print(f'Using fallback client: {intelligence.using_fallback_client}')
    
    # Test a simple conversation
    print('\n🧪 Testing conversation...')
    intelligence.generate("Hello, I'm ready for the interview", "TestUser")
    
    print('\n🧪 Testing NLP conversation...')
    intelligence.generate("NLP stands for natural language processing", "TestUser")
    
    print('\n✅ Test completed successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
