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
    print("🧪 Testing agent name consistency and formatting...")
    
    # Create mock pubsub
    pubsub = MockPubSub()
    
    # Create intelligence client with specific agent name
    intelligence = GroqIntelligence(
        api_key='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', 
        tts=MockTTS(),
        agent_name="AI/ML Expert"  # Test with AI/ML Expert name
    )
    
    # Set pubsub
    intelligence.set_pubsub(pubsub)
    
    print(f'✅ GroqIntelligence created with agent name: "{intelligence.agent_name}"')
    
    # Test 1: Agent introduction with consistent naming
    print('\n🎯 Test 1: Agent introduction...')
    intelligence.generate("Hello! I'm AI/ML Expert, your AI interviewer.", "AI/ML Expert", is_agent_introduction=True)
    
    # Test 2: Question with formatting (simulating the issue)
    print('\n🎯 Test 2: Question with formatting symbols...')
    test_question = "**Question:** What does NLP stand for? **Type:** Concept **Topic:** Applications"
    cleaned = intelligence._clean_response_for_tts(test_question)
    print(f'Raw question: "{test_question}"')
    print(f'Cleaned: "{cleaned}"')
    
    # Test 3: Regular conversation response
    print('\n🎯 Test 3: Regular conversation...')
    intelligence.generate("I want to learn about machine learning", "TestUser")
    
    print(f'\n📊 Total chat messages: {len(pubsub.messages)}')
    print('📝 Chat messages:')
    for i, msg in enumerate(pubsub.messages, 1):
        print(f'  {i}. {msg}')
    
    # Check if all messages use the same agent name
    agent_names = set()
    for msg in pubsub.messages:
        if ']:' in msg:
            name = msg.split(']:')[0].replace('[', '')
            agent_names.add(name)
    
    print(f'\n📋 Agent names used: {list(agent_names)}')
    if len(agent_names) == 1:
        print('✅ Consistent agent naming!')
    else:
        print('❌ Inconsistent agent naming found!')
    
    print('\n✅ Test completed!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
