import time
from typing import Optional

from groq import Groq

from intelligence.adaptive_policy import InterviewFlowManager
from intelligence.intelligence import Intelligence
from tts.tts import TTS


class GroqIntelligence(Intelligence):
    def __init__(self, api_key: str, tts: TTS, model: Optional[str] = None, system_prompt: Optional[str] = None, questions_manager=None, agent_name: str = "AI Interviewer"):
        # Handle Groq client initialization with version compatibility
        self.agent_name = agent_name  # Store agent name for consistent labeling
        self.using_fallback_client = False
        
        print("🔧 [DEBUG] Attempting to initialize Groq client...")
        try:
            self.client = Groq(api_key=api_key)
            print("✅ Groq client initialized successfully")
        except TypeError as e:
            print(f"⚠️ Groq client TypeError: {e}")
            if "proxies" in str(e):
                print("🔄 Trying alternative initialization methods...")
                # Try alternative initialization for compatibility
                import os
                original_key = os.environ.get("GROQ_API_KEY")
                os.environ["GROQ_API_KEY"] = api_key
                try:
                    self.client = Groq()
                    print("✅ Groq client initialized with environment variable")
                except Exception as fallback_error:
                    print(f"⚠️ Environment variable method failed: {fallback_error}")
                    print("🔄 Using fallback client mode")
                    self.client = self._create_fallback_client(api_key)
                    self.using_fallback_client = True
                finally:
                    if original_key:
                        os.environ["GROQ_API_KEY"] = original_key
                    elif "GROQ_API_KEY" in os.environ:
                        del os.environ["GROQ_API_KEY"]
            else:
                print(f"⚠️ Other TypeError in Groq client: {e}")
                print("🔄 Using fallback client mode")
                self.client = self._create_fallback_client(api_key)
                self.using_fallback_client = True
        except Exception as e:
            print(f"⚠️ General error initializing Groq client: {e}")
            print("🔄 Using fallback client mode")
            self.client = self._create_fallback_client(api_key)
            self.using_fallback_client = True

        self.tts = tts
        self.chat_history = []
        self.model = model or "openai/gpt-oss-120b"  # Default to GPT OSS 120B model
        self.questions_manager = questions_manager  # Store questions manager reference
        self.current_question_index = 0  # Track current question
        self.questions_used = []  # Track which questions have been used
        
        # Initialize LangGraph-based Adaptive Interview Policy with error handling
        print("🔧 [DEBUG] Initializing adaptive policy...")
        try:
            self.flow_manager = InterviewFlowManager(groq_api_key=api_key, questions_manager=questions_manager)
            self.adaptive_policy_enabled = True  # RE-ENABLED
            print("✅ Adaptive Interview Policy initialized successfully")
        except Exception as e:
            print(f"⚠️ Adaptive Policy initialization failed: {e}")
            print("🔄 Continuing with standard interview flow...")
            self.flow_manager = None
            self.adaptive_policy_enabled = False
        
        self.current_question = None
        self.current_question_category = "technical"
        self.current_question_difficulty = "medium"
        self.waiting_for_response = False
        
        self.system_prompt = system_prompt or """You are an intelligent interviewer conducting an interview. You adapt your questions and style based on the pre-loaded question set provided to you.

IMPORTANT CONVERSATION FLOW:
- When you receive a SUGGESTED NEXT QUESTION, use that as your primary question to ask
- When a candidate gives a brief response or asks for clarification, provide helpful follow-up instead of repeating questions
- When a candidate says "next" or similar, move to the next topic rather than elaborating on the current one
- Listen carefully to what the candidate is actually saying and respond appropriately
- NEVER ask the same question twice - always move forward to new topics

Interview Guidelines:
- Follow the flow of your pre-loaded questions when suggestions are provided
- Ask one question at a time and wait for the candidate's response
- Be conversational and engaging while following the structured question flow
- Adapt your tone and style to match the theme of the questions provided
- If questions are about specific topics (like TV shows, movies, etc.), embrace that theme completely
- CRITICAL: NEVER repeat the same question - if already asked, either provide context or move on to a different question

CRITICAL OUTPUT FORMATTING RULES:
- NEVER use asterisks (*), markdown formatting, or structural elements like "Question:", "Type:", "Topic:"
- NEVER include meta-commentary, stage directions, or notes meant for the LLM
- Speak directly to the candidate as if you are having a natural conversation
- Avoid filler words like "um", "uh", "well", "you know", "basically", "actually", "like"
- No parenthetical comments or asides
- Use natural, conversational language that flows well when spoken aloud
- Keep responses direct and clear without unnecessary qualifiers
- Remove all formatting symbols before speaking

RESPONSE HANDLING:
- If candidate gives a complete answer, acknowledge it and move to next topic
- If candidate gives brief answer, ask for specific examples or elaboration
- If candidate asks "what edge cases" or similar, provide specific examples related to the topic
- If candidate says "next", move to a different question/topic
- NEVER repeat questions that have already been asked - always progress forward

Communication Style:
- Maintain a conversational, engaging tone throughout
- Ask follow-up questions when appropriate
- Show genuine interest in the candidate's responses
- Be flexible and adapt to the conversation flow
- Keep responses focused and concise (2-4 sentences typically)

Remember: Your primary job is to ask the questions from your pre-loaded question set. When you receive a suggested question, that becomes your next question to ask. Adapt the wording naturally but use that specific question content. Never repeat previously asked questions."""

        self.pubsub = None
    
    def set_pubsub(self, pubsub):
        self.pubsub = pubsub

    def build_messages(self, text: str, sender_name: str):
        # Build the message with proper context
        human_message = {
            "role": "user",
            "content": f"Candidate ({sender_name}): {text}",
        }

        # Add message to history
        self.chat_history.append(human_message)

        # Local chat history for context (keep more messages for interview continuity)
        chat_history = []

        # Add system message with interviewer context
        chat_history.append(
            {
                "role": "system",
                "content": self.system_prompt,
            }
        )

        # Add conversation history (last 40 messages for better interview flow and context retention)
        chat_history = chat_history + self.chat_history[-40:]

        # Return local chat history
        return chat_history
    
    def add_response(self, text):
        ai_message = {
            "role": "assistant",
            "content": text,
        }

        self.chat_history.append(ai_message)

    def text_generator(self, response):
        """Generate text chunks from streaming response"""
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def generate(self, text: str, sender_name: str, is_agent_introduction: bool = False):
        print(f"🎯 [GENERATE] Starting response generation for: {text[:50]}...")
        generation_start_time = time.time()
        
        try:
            # Handle agent introduction directly without LLM processing
            if is_agent_introduction:
                print(f"[{sender_name}]: {text}")
                
                # Publish introduction to meeting chat
                if self.pubsub is not None:
                    self.pubsub(message=f"[{sender_name}]: {text}")
                
                # Send directly to TTS for agent introduction
                if len(text) > 500:
                    chunks = self._split_response_for_tts(text, max_chunk_length=400)
                    for chunk in chunks:
                        self.tts.generate(text=chunk)
                else:
                    self.tts.generate(text=text)
                
                # Add to chat history
                self.chat_history.append({
                    "role": "assistant",
                    "content": text
                })
                
                # Start with first question after introduction
                self._start_first_question()
                return
            
            # Emergency timeout check - if any processing takes longer than 15 seconds, force fallback
            def emergency_fallback():
                elapsed = time.time() - generation_start_time
                if elapsed > 15.0:
                    print(f"🚨 [EMERGENCY] Processing taking too long ({elapsed:.1f}s), forcing fallback!")
                    self._handle_regular_conversation(text, sender_name)
                    return True
                return False
            
            # If we're waiting for a response to a question, use adaptive policy
            if self.waiting_for_response and self.current_question:
                print("🔄 [GENERATE] Using adaptive policy...")
                if emergency_fallback():
                    return
                self._handle_candidate_response_with_adaptive_policy(text, sender_name)
                return
            
            # Fallback to regular conversation flow
            print("🔄 [GENERATE] Using regular conversation...")
            if emergency_fallback():
                return
            self._handle_regular_conversation(text, sender_name)
            
            # Log total processing time
            total_time = time.time() - generation_start_time
            print(f"⏱️ [GENERATE] Total processing time: {total_time:.2f} seconds")
            return

        except Exception as e:
            print(f"Error generating response with Groq: {e}")
            print(f"Error type: {type(e).__name__}")
            if self.using_fallback_client:
                print("🔧 [DEBUG] Using fallback client - error in fallback implementation")
            else:
                print("🔧 [DEBUG] Using real Groq client - API or network error")
            
            # Import traceback for detailed error information
            import traceback
            traceback.print_exc()
            
            # Improved fallback response for interviewer context
            fallback_text = "I'm experiencing some technical difficulties. Let's continue with the next question."
            self.tts.generate(text=fallback_text)
            if self.pubsub is not None:
                self.pubsub(message=f"[{self.agent_name}]: {fallback_text}")

    def _split_response_for_tts(self, text: str, max_chunk_length: int = 400):
        """Split long responses into larger chunks for better TTS delivery while preserving context"""
        if len(text) <= max_chunk_length:
            return [text]
        
        # Try to split by paragraphs first (double newlines)
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            chunks = []
            current_chunk = ""
            
            for paragraph in paragraphs:
                if len(current_chunk + paragraph + '\n\n') <= max_chunk_length:
                    current_chunk += paragraph + '\n\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Fallback to sentence splitting with larger chunks
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') <= max_chunk_length:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _clean_response_for_tts(self, text: str) -> str:
        """Enhanced cleaning for TTS-friendly output - removes all unwanted symbols and formatting"""
        import re

        # Remove question formatting patterns first
        text = re.sub(r'\*\*Question:\*\*\s*', '', text)
        text = re.sub(r'\*\*Type:\*\*\s*[^\*]*', '', text)
        text = re.sub(r'\*\*Topic:\*\*\s*[^\*]*', '', text)
        text = re.sub(r'Question:\s*', '', text)
        text = re.sub(r'Type:\s*[^\n]*', '', text)
        text = re.sub(r'Topic:\s*[^\n]*', '', text)
        
        # Aggressive removal of ALL markdown and unwanted symbols
        text = re.sub(r'[*#`_~\[\]{}|\\]', '', text)  # Remove all markdown symbols
        
        # Remove any text in parentheses or brackets (stage directions, meta comments)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        
        # Remove numbers at start of lines (list formatting)
        text = re.sub(r'^\d+\.?\s*', '', text, flags=re.MULTILINE)
        
        # Remove bullet points and dashes
        text = re.sub(r'^[-•→◦]\s*', '', text, flags=re.MULTILINE)
        
        # Remove common filler words that slow down speech
        filler_patterns = [
            r'\b(um|uh|er|ah|hmm|well|so|okay|now)\b\s*',
            r'\byou know\b\s*',
            r'\bbasically\b\s*',
            r'\bactually\b\s*(?!implement|code|work)',
            r'\blike\b\s*(?!this|that|a)',
            r'\bkind of\b\s*',
            r'\bsort of\b\s*',
        ]
        
        for pattern in filler_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove meta-commentary and transition phrases
        meta_patterns = [
            r'let me (think|see|explain|tell you)\s*[.,]?\s*',
            r'so (basically|essentially|in other words)\s*[.,]?\s*',
            r'what (I mean is|this means is)\s*[.,]?\s*',
            r'(essentially|basically|fundamentally)\s*[.,]?\s*',
            r'(to summarize|in summary|in conclusion)\s*[.,]?\s*',
            r'^\*.*?\*\s*',  # Remove leading asterisk comments
            r'\*.*?\*',      # Remove any remaining asterisk comments
            r'\bnow\s+(?:let\'s|let\s+us|we\s+will|we\s+should)\b',  # Remove "now let's" transitions
        ]
        
        for pattern in meta_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up excessive punctuation and whitespace
        text = re.sub(r'[.,]{2,}', '.', text)  # Multiple periods to single
        text = re.sub(r'\s*[.,]\s*[.,]\s*', '. ', text)  # Clean up comma/period combos
        text = re.sub(r'\s*,\s*,', ',', text)  # Remove double commas
        text = re.sub(r'\s*\.\s*\.', '.', text)  # Remove double periods
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'^[,.\s]+', '', text)  # Remove leading punctuation
        text = re.sub(r'[,.\s]+$', '.', text)  # Ensure proper ending
        
        # Ensure sentences end properly
        text = text.strip()
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text
    
    def _get_questions_from_manager(self):
        """Helper to get questions from either file or API manager"""
        if not self.questions_manager:
            return []
        
        # File-based manager
        if hasattr(self.questions_manager, 'get_current_questions'):
            return self.questions_manager.get_current_questions() or []
        
        # API-based manager  
        elif hasattr(self.questions_manager, 'questions_data'):
            if self.questions_manager.questions_data and 'questions' in self.questions_manager.questions_data:
                # Convert API questions to a compatible format
                api_questions = self.questions_manager.questions_data['questions']
                compatible_questions = []
                for q in api_questions:
                    class APIQuestion:
                        def __init__(self, text, category="general", difficulty="medium"):
                            self.text = text
                            self.category = type('Category', (), {'value': category})()
                            self.difficulty = difficulty
                    
                    question_text = q.get('text', q.get('question', ''))
                    category = q.get('category', 'general')
                    difficulty = q.get('difficulty', 'medium')
                    compatible_questions.append(APIQuestion(question_text, category, difficulty))
                
                return compatible_questions
        
        return []
    
    def get_next_question(self, category=None):
        """Get the next structured question from the question manager"""
        if not self.questions_manager:
            return None
        
        questions = self._get_questions_from_manager()
        if not questions:
            return None
        
        # Filter by category if specified
        available_questions = []
        for i, question in enumerate(questions):
            if i not in self.questions_used:
                if category is None or question.category.value.lower() == category.lower():
                    available_questions.append((i, question))
        
        if not available_questions:
            return None
        
        # Return the first available question
        index, question = available_questions[0]
        self.questions_used.append(index)
        return question
    
    def get_questions_by_category(self, category):
        """Get all questions for a specific category"""
        if not self.questions_manager:
            return []
        
        questions = self._get_questions_from_manager()
        return [q for q in questions if q.category.value.lower() == category.lower()]
    
    def get_interview_progress(self):
        """Get current interview progress information"""
        if not self.questions_manager:
            return {"using_structured_questions": False}
        
        questions = self._get_questions_from_manager()
        total_questions = len(questions)
        used_questions = len(self.questions_used)
        
        return {
            "using_structured_questions": True,
            "total_questions": total_questions,
            "questions_used": used_questions,
            "progress_percentage": (used_questions / total_questions * 100) if total_questions > 0 else 0,
            "questions_remaining": total_questions - used_questions
        }
    
    def reset_question_progress(self):
        """Reset question tracking for a new interview"""
        self.questions_used = []
        self.current_question_index = 0
    
    def _get_suggested_question(self, user_text: str, sender_name: str):
        """Get suggested question based on conversation context and loaded questions"""
        if not self.questions_manager:
            return None
        
        questions = self._get_questions_from_manager()
        if not questions:
            return None
        
        # Get already used questions from different tracking systems
        used_questions_texts = set()
        used_question_indices = set()
        
        # From flow manager
        if self.flow_manager and hasattr(self.flow_manager, 'session_context'):
            used_questions_texts.update(self.flow_manager.session_context.get('questions_used', []))
        
        # From instance tracking
        if hasattr(self, 'questions_used'):
            used_question_indices.update(self.questions_used)
        
        # Also check current question to avoid repetition
        if self.current_question:
            used_questions_texts.add(self.current_question)
        
        # Determine conversation stage based on chat history
        conversation_length = len(self.chat_history)
        
        # Select questions that haven't been used
        available_questions = []
        for i, q in enumerate(questions):
            if (q.text not in used_questions_texts and 
                i not in used_question_indices):
                available_questions.append((i, q))
        
        if not available_questions:
            print("⚠️ [QUESTION SELECTION] No unused questions available")
            return None
        
        # First interaction - start with introduction/technical
        if conversation_length <= 2:
            intro_questions = [(i, q) for i, q in available_questions 
                             if q.category.value.lower() in ['introduction', 'technical']]
            if intro_questions:
                index, question = intro_questions[0]
                self._mark_question_used(index, question)
                return question
        
        # Middle conversation - use technical, coding, system design
        elif conversation_length <= 10:
            categories = ['technical', 'coding', 'system_design']
            for category in categories:
                cat_questions = [(i, q) for i, q in available_questions 
                               if q.category.value.lower() == category]
                if cat_questions:
                    index, question = cat_questions[0]
                    self._mark_question_used(index, question)
                    return question
        
        # Later conversation - behavioral and closing
        else:
            categories = ['behavioral', 'closing']
            for category in categories:
                cat_questions = [(i, q) for i, q in available_questions 
                               if q.category.value.lower() == category]
                if cat_questions:
                    index, question = cat_questions[0]
                    self._mark_question_used(index, question)
                    return question
        
        # If no category-specific questions found, use first available
        if available_questions:
            index, question = available_questions[0]
            self._mark_question_used(index, question)
            return question
        
        return None
    
    def _mark_question_used(self, index: int, question):
        """Mark a question as used in all tracking systems"""
        # Mark in instance tracking
        if not hasattr(self, 'questions_used'):
            self.questions_used = []
        if index not in self.questions_used:
            self.questions_used.append(index)
        
        # Mark in flow manager
        if self.flow_manager and hasattr(self.flow_manager, 'session_context'):
            if question.text not in self.flow_manager.session_context.get('questions_used', []):
                self.flow_manager.session_context.setdefault('questions_used', []).append(question.text)
        
        print(f"📝 [QUESTION TRACKING] Marked question as used: {question.text[:50]}...")

    def _start_first_question(self):
        """Start the interview with the first question"""
        if self.questions_manager:
            questions = self._get_questions_from_manager()
            if questions:
                # Find an appropriate first question - prefer introduction/technical
                first_question = None
                for q in questions:
                    if q.category.value.lower() in ['introduction', 'technical']:
                        first_question = q
                        break
                
                # If no intro/technical question, use first available
                if not first_question:
                    first_question = questions[0]
                
                self.current_question = first_question.text
                self.current_question_category = first_question.category.value
                self.current_question_difficulty = first_question.difficulty.value
                self.waiting_for_response = True
                
                # Mark this question as used
                if hasattr(self, 'questions_used'):
                    for i, q in enumerate(questions):
                        if q.id == first_question.id and i not in self.questions_used:
                            self.questions_used.append(i)
                            break
                
                # Update flow manager context if available
                if self.flow_manager:
                    self.flow_manager.session_context['questions_used'].append(first_question.text)
                
                print(f"🎯 [ADAPTIVE POLICY] Started first question: {self.current_question}")
    
    def _handle_candidate_response_with_adaptive_policy(self, response: str, candidate_name: str):
        """Handle candidate response using LangGraph adaptive policy"""
        
        # Check if adaptive policy is available and not disabled
        if not self.adaptive_policy_enabled or self.flow_manager is None:
            print("⚠️ Adaptive policy not available, falling back to regular conversation")
            self._handle_regular_conversation(response, candidate_name)
            return
        
        # Emergency disable adaptive policy if it's causing delays
        if hasattr(self, '_adaptive_policy_failed_count') and self._adaptive_policy_failed_count > 2:
            print("🚨 Adaptive policy disabled due to repeated failures, using regular conversation")
            self._handle_regular_conversation(response, candidate_name)
            return
        
        if not self.current_question:
            print("⚠️ No current question set, falling back to regular conversation")
            self._handle_regular_conversation(response, candidate_name)
            return
        
        print(f"🔍 [ADAPTIVE POLICY] Analyzing response: {response[:100]}...")
        
        try:
            # Add timeout for processing to prevent hanging
            import signal
            import threading
            
            def timeout_handler():
                print("⏰ [ADAPTIVE POLICY] Processing timeout, falling back...")
                return None
            
            print("🔄 [ADAPTIVE POLICY] Starting response processing...")
            start_time = time.time()
            
            # Process response through the adaptive policy graph
            result = self.flow_manager.process_response(
                current_question=self.current_question,
                candidate_response=response,
                candidate_name=candidate_name,
                question_category=self.current_question_category,
                question_difficulty=self.current_question_difficulty
            )
            
            processing_time = time.time() - start_time
            print(f"⏱️ [ADAPTIVE POLICY] Processing took {processing_time:.2f} seconds")
            
            if result is None:
                print("⚠️ [ADAPTIVE POLICY] No result returned, falling back...")
                self._handle_regular_conversation(response, candidate_name)
                return
            
            # Log the decision
            print(f"📊 [ADAPTIVE POLICY] Decision: {result['action']}")
            print(f"💡 [ADAPTIVE POLICY] Explanation: {result['explanation']}")
            
            if result['analysis']:
                analysis = result['analysis']
                print(f"📈 [ADAPTIVE POLICY] Quality: {analysis.get('quality', 'unknown')}, "
                      f"Confidence: {analysis.get('confidence', 0):.2f}")
            
            # Handle the decision
            action = result['action']
            interviewer_response = result['response']
            
            if action in ['ask_followup', 'provide_guidance', 'clarify_question']:
                # Stay with current question, ask follow-up
                print(f"🔄 [ADAPTIVE POLICY] Asking follow-up question")
                self.waiting_for_response = True
                
            elif action == 'move_to_next':
                # Move to next question
                print(f"➡️ [ADAPTIVE POLICY] Moving to next question")
                self._move_to_next_question()
                
            elif action == 'end_interview':
                # End the interview
                print(f"🏁 [ADAPTIVE POLICY] Ending interview")
                self.waiting_for_response = False
                self.current_question = None
            
            # Clean and send response to TTS
            cleaned_response = self._clean_response_for_tts(interviewer_response)
            self._send_to_tts(cleaned_response)
            
            # Update chat history
            self.chat_history.append({
                "role": "user",
                "content": response
            })
            self.chat_history.append({
                "role": "assistant", 
                "content": cleaned_response
            })
            
            # Show session stats
            stats = self.flow_manager.get_session_stats()
            print(f"📊 [SESSION STATS] Questions: {stats['total_questions']}, "
                  f"Time: {stats['elapsed_time_minutes']:.1f}min, "
                  f"Remaining: {stats['questions_remaining']}")
                  
        except Exception as e:
            print(f"❌ [ADAPTIVE POLICY] Error: {e}")
            print("🔄 Falling back to regular conversation...")
            import traceback
            traceback.print_exc()
            
            # Track failures to disable adaptive policy if it keeps failing
            if not hasattr(self, '_adaptive_policy_failed_count'):
                self._adaptive_policy_failed_count = 0
            self._adaptive_policy_failed_count += 1
            
            self._handle_regular_conversation(response, candidate_name)
    
    def _move_to_next_question(self):
        """Move to the next question in the interview"""
        
        if self.questions_manager:
            questions = self._get_questions_from_manager()
            
            # Get questions that haven't been used yet
            if self.flow_manager and hasattr(self.flow_manager, 'session_context'):
                questions_used = self.flow_manager.session_context.get('questions_used', [])
                unused_questions = [q for q in questions if q.text not in questions_used]
            else:
                # Fallback to instance tracking
                used_indices = getattr(self, 'questions_used', [])
                unused_questions = [q for i, q in enumerate(questions) if i not in used_indices]
            
            if unused_questions:
                # Select next appropriate question
                next_question = unused_questions[0]
                
                # Update current question tracking
                self.current_question = next_question.text
                self.current_question_category = next_question.category.value
                self.current_question_difficulty = next_question.difficulty.value
                self.waiting_for_response = True
                
                # Mark as used in both tracking systems
                if self.flow_manager:
                    self.flow_manager.session_context['questions_used'].append(next_question.text)
                
                if hasattr(self, 'questions_used'):
                    for i, q in enumerate(questions):
                        if q.id == next_question.id and i not in self.questions_used:
                            self.questions_used.append(i)
                            break
                
                print(f"🆕 [ADAPTIVE POLICY] Next question: {self.current_question}")
            else:
                # No more questions available
                self.current_question = None
                self.waiting_for_response = False
                print(f"✅ [ADAPTIVE POLICY] No more questions available - interview ending")
        else:
            # No questions manager - end interview
            self.current_question = None
            self.waiting_for_response = False
            print(f"✅ [ADAPTIVE POLICY] No questions manager - interview ending")
    
    def _handle_regular_conversation(self, text: str, sender_name: str):
        """Handle regular conversation flow (fallback)"""
        
        # Check if we should suggest a specific question from the loaded questions
        suggested_question = self._get_suggested_question(text, sender_name)
        
        # build message history
        messages = self.build_messages(text, sender_name=sender_name)
        
        # Add suggested question context if available
        if suggested_question:
            question_context = {
                "role": "system",
                "content": f"SUGGESTED NEXT QUESTION: Consider asking this specific question: '{suggested_question.text}' (Category: {suggested_question.category.value}, Difficulty: {suggested_question.difficulty.value}). This is from your pre-loaded question set. You can adapt the wording naturally but use this as your primary question to ask."
            }
            messages.append(question_context)

        # generate llm completion using Groq with optimized parameters for faster responses
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,  # More controlled temperature for professional responses
            max_completion_tokens=1024,  # Reduced for faster response generation
            top_p=0.9,  # More focused responses
            reasoning_effort="medium",
            stream=False,  # Use non-streaming for complete responses
            stop=None
        )

        # Extract response text directly from non-streaming response
        response_text = completion.choices[0].message.content.strip()
        
        # Clean the response for TTS
        cleaned_response = self._clean_response_for_tts(response_text)

        if cleaned_response:
            self._send_to_tts(cleaned_response)
            
            # Add to chat history
            self.chat_history.append({
                "role": "user",
                "content": text
            })
            self.chat_history.append({
                "role": "assistant",
                "content": cleaned_response
            })
            
            # Set up for adaptive policy if this was a question
            if suggested_question:
                self.current_question = suggested_question.text
                self.current_question_category = suggested_question.category.value
                self.current_question_difficulty = suggested_question.difficulty.value
                self.waiting_for_response = True
                print(f"🎯 [ADAPTIVE POLICY] Set up question tracking: {self.current_question}")
    
    def _send_to_tts(self, text: str):
        """Send text to TTS with chunking if needed and publish to meeting chat"""
        if len(text) > 500:
            chunks = self._split_response_for_tts(text, max_chunk_length=400)
            print(f"[{self.agent_name}]: {text}")
            
            # Publish the full response to meeting chat
            if self.pubsub is not None:
                self.pubsub(message=f"[{self.agent_name}]: {text}")
            
            for i, chunk in enumerate(chunks):
                if i > 0:
                    import time
                    time.sleep(0.1)  # Reduced delay for faster response
                self.tts.generate(text=chunk)
        else:
            print(f"[{self.agent_name}]: {text}")
            self.tts.generate(text=text)
            
            # Publish to meeting chat
            if self.pubsub is not None:
                self.pubsub(message=f"[{self.agent_name}]: {text}")
    
    def _create_fallback_client(self, api_key: str):
        """Create a fallback client that provides basic functionality"""
        class FallbackGroqClient:
            def __init__(self, api_key):
                self.api_key = api_key
                self.conversation_count = 0
                
            class ChatCompletions:
                def __init__(self, api_key):
                    self.api_key = api_key
                    self.parent = None
                    
                def create(self, model, messages, temperature=0.7, max_completion_tokens=2048, 
                          top_p=0.9, reasoning_effort="medium", stream=False, stop=None):
                    # Get the last message for context
                    last_message = messages[-1].get('content', '') if messages else ''
                    
                    # Increment conversation counter
                    if self.parent:
                        self.parent.conversation_count += 1
                    
                    # Handle follow-up questions and edge cases
                    if 'next' in last_message.lower():
                        response_text = "Great! Let's move to the next topic. Can you tell me about your experience with data structures and algorithms?"
                    elif any(word in last_message.lower() for word in ['edge case', 'edge cases', 'what about']):
                        response_text = "Good question! For NLP, some common edge cases include handling multiple languages, dealing with typos and abbreviations, processing emojis and special characters, and managing very short or very long texts."
                    elif any(word in last_message.lower() for word in ['elaborate', 'more detail', 'explain more']):
                        response_text = "Could you provide a specific example from your experience? What challenges did you encounter and how did you solve them?"
                    elif 'hello' in last_message.lower() or 'ready' in last_message.lower():
                        response_text = "Great! Let's begin with a technical question. Can you explain what algorithms you're most comfortable with?"
                    elif any(word in last_message.lower() for word in ['algorithm', 'sort', 'search', 'complexity']):
                        response_text = "That's a good explanation. Can you walk me through the time complexity analysis of that algorithm?"
                    elif any(word in last_message.lower() for word in ['nlp', 'natural language', 'processing']):
                        response_text = "Excellent! Since you mentioned NLP, can you explain how you would approach building a text classification system?"
                    elif any(word in last_message.lower() for word in ['python', 'programming', 'code']):
                        response_text = "Good! Now let's discuss a coding problem. How would you reverse a linked list iteratively?"
                    elif any(word in last_message.lower() for word in ['experience', 'project', 'work']):
                        response_text = "That sounds like valuable experience. Can you tell me about a challenging technical problem you solved recently?"
                    elif any(word in last_message.lower() for word in ['system', 'design', 'architecture']):
                        response_text = "Interesting approach. How would you handle scalability and performance in that system?"
                    elif len(last_message.split()) > 20:  # Longer responses
                        response_text = "Thank you for that detailed explanation. Let's move to our next question. What's your experience with database optimization?"
                    else:
                        # Default responses that keep the interview flowing
                        fallback_responses = [
                            "Can you elaborate on that with a specific example?",
                            "That's interesting. How would you implement that in practice?", 
                            "Good point. What challenges did you face with that approach?",
                            "Let's explore that further. Can you walk me through your thought process?",
                            "Now let's discuss a different topic. What's your experience with data structures?"
                        ]
                        response_index = (self.parent.conversation_count if self.parent else 0) % len(fallback_responses)
                        response_text = fallback_responses[response_index]
                    
                    # Mock response object
                    class MockChoice:
                        def __init__(self, content):
                            self.message = type('obj', (object,), {'content': content})()
                    
                    class MockResponse:
                        def __init__(self, content):
                            self.choices = [MockChoice(content)]
                    
                    return MockResponse(response_text)
            
            class Chat:
                def __init__(self, api_key):
                    self.api_key = api_key
                    self.completions = FallbackGroqClient.ChatCompletions(api_key)
            
            def __init__(self, api_key):
                self.api_key = api_key
                self.conversation_count = 0
                self.chat = self.Chat(api_key)
                # Set parent reference for conversation tracking
                self.chat.completions.parent = self
        
        return FallbackGroqClient(api_key)
