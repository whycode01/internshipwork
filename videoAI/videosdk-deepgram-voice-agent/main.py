#!/usr/bin/env python3
"""
VideoSDK realtime AI Agent | Interviewer
"""
import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import traceback

from dotenv import load_dotenv
from groq import Groq

from agent.agent import AIInterviewer
from agent.audio_stream_track import CustomAudioStreamTrack
from intelligence.groq_intelligence import GroqIntelligence
from questions.question_api_manager import QuestionAPIManager
from questions.question_upload import QuestionFileManager
from stt.deepgram_stt import DeepgramSTT
from tts.deepgram_tts import DeepgramTTS

load_dotenv()
loop = asyncio.new_event_loop()
room_id = os.getenv("ROOM_ID")
auth_token = os.getenv("AUTH_TOKEN")
language = os.getenv("LANGUAGE", "en-US")
stt_api_key = os.getenv("DEEPGRAM_API_KEY")
tts_api_key = os.getenv("ELEVENLABS_API_KEY")
llm_api_key = os.getenv("GROQ_API_KEY")
agent: AIInterviewer = None
stopped: bool = False
question_manager = None  # Can be either QuestionFileManager or QuestionAPIManager
args = None  # Global args for accessing job_id and candidate_id

class Bcolors:
    """Color class for terminal output"""
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='VideoSDK AI Interviewer Agent')
    
    # API mode arguments
    parser.add_argument('--job-id', type=str, help='Job ID for API-based question fetching')
    parser.add_argument('--candidate-id', type=str, help='Candidate ID for API-based question fetching')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000', 
                       help='Base API URL for questions API (default: http://localhost:8000)')
    
    # File mode argument (positional)
    parser.add_argument('question_file', nargs='?', help='Path to questions file (.md)')
    
    return parser.parse_args()

def setup_questions():
    """Setup question manager and load questions from API or file"""
    global question_manager, args
    
    args = parse_arguments()
    
    # Check if API mode is requested
    if args.job_id and args.candidate_id:
        print(f"{Bcolors.HEADER}🌐 API Mode: Loading questions for Job ID: {args.job_id}, Candidate ID: {args.candidate_id}")
        question_manager = QuestionAPIManager(base_url=args.api_url)
        
        questions_data = question_manager.fetch_questions(args.job_id, args.candidate_id)
        if questions_data:
            print(f"{Bcolors.OKGREEN}✅ Questions loaded successfully from API!")
            print(f"   📊 Total questions: {len(questions_data.get('questions', []))}")
            if 'metadata' in questions_data:
                metadata = questions_data['metadata']
                print(f"   💼 Job: {metadata.get('job_title', 'N/A')}")
                print(f"   👤 Candidate: {metadata.get('candidate_name', 'N/A')}")
                print(f"   🎯 Interview Type: {metadata.get('interview_type', 'N/A')}")
        else:
            print(f"{Bcolors.FAIL}❌ Failed to load questions from API")
            question_manager = None
            
    # Check if file mode is requested
    elif args.question_file:
        print(f"{Bcolors.HEADER}📁 File Mode: Loading questions from: {args.question_file}")
        question_manager = QuestionFileManager()
        
        if question_manager.upload_questions_file(args.question_file):
            summary = question_manager.get_questions_summary()
            print(f"{Bcolors.OKGREEN}✅ Questions loaded successfully!")
            print(f"   📊 Total questions: {summary['total']}")
            print(f"   📂 Categories: {list(summary['categories'].keys())}")
            print(f"   🎯 Difficulties: {list(summary['difficulties'].keys())}")
        else:
            print(f"{Bcolors.FAIL}❌ Failed to load questions file")
            question_manager = None
            
    else:
        # Try to load default questions if available (legacy support)
        question_manager = QuestionFileManager()
        uploaded_files = question_manager.list_uploaded_files()
        if uploaded_files:
            print(f"{Bcolors.HEADER}Available question files: {uploaded_files}")
            if "sample_questions.md" in uploaded_files:
                question_manager.load_existing_file("sample_questions.md")
                print(f"{Bcolors.OKGREEN}✅ Loaded default sample questions")
            else:
                question_manager.load_existing_file(uploaded_files[0])
                print(f"{Bcolors.OKGREEN}✅ Loaded {uploaded_files[0]}")
        else:
            print(f"{Bcolors.HEADER}💡 No questions provided. Usage:")
            print("   API Mode: python main.py --job-id <JOB_ID> --candidate-id <CANDIDATE_ID>")
            print("   File Mode: python main.py <path_to_questions.md>")
    
    return question_manager

def detect_agent_personality_with_llm(questions_mgr):
    """Use LLM to intelligently detect the appropriate agent personality based on question content"""
    if not questions_mgr:
        return "general_interviewer"
    
    # Handle both API and file-based question managers
    if hasattr(questions_mgr, 'get_current_questions'):
        # File-based manager
        questions = questions_mgr.get_current_questions()
        if not questions:
            return "general_interviewer"
        questions_text = "\n".join([f"Q{i+1}: {q.text}" for i, q in enumerate(questions[:10])])
        
    elif hasattr(questions_mgr, 'questions_data'):
        # API-based manager
        if not questions_mgr.questions_data or 'questions' not in questions_mgr.questions_data:
            return "general_interviewer"
        questions = questions_mgr.questions_data['questions'][:10]  # Limit to first 10
        questions_text = "\n".join([f"Q{i+1}: {q.get('text', q.get('question', ''))}" for i, q in enumerate(questions)])
        
        # Check if personality is provided in metadata
        metadata = questions_mgr.questions_data.get('metadata', {})
        
        # Enhanced mapping for corporate and other interview types
        if 'interview_type' in metadata:
            interview_type = metadata['interview_type'].lower()
            type_mapping = {
                'python': 'python_expert',
                'python_technical': 'python_expert',
                'ai': 'ai_ml_expert',
                'ai_ml': 'ai_ml_expert',
                'machine learning': 'ai_ml_expert',
                'dsa': 'dsa_expert',
                'algorithms': 'dsa_expert',
                'system design': 'system_design_expert',
                'sde': 'sde_interviewer',
                'software engineer': 'sde_interviewer',
                'technical': 'sde_interviewer',
                'corporate': 'corporate_interviewer',
                'corporate_interview': 'corporate_interviewer',
                'finance': 'corporate_interviewer',
                'financial': 'corporate_interviewer',
                'business': 'corporate_interviewer',
                'marketing': 'corporate_interviewer',
                'general': 'general_interviewer'
            }
            for key, personality in type_mapping.items():
                if key in interview_type:
                    print(f"🎯 Personality detected from metadata: {personality} (interview_type: {interview_type})")
                    return personality
        
        # Also check job_category from metadata
        if 'job_category' in metadata:
            job_category = metadata['job_category'].lower()
            print(f"🔍 [DEBUG] Checking job_category: '{job_category}'")
            category_mapping = {
                'corporate': 'corporate_interviewer',
                'corporate_roles': 'corporate_interviewer',
                'finance': 'corporate_interviewer',
                'financial': 'corporate_interviewer',
                'business': 'corporate_interviewer',
                'marketing': 'corporate_interviewer',
                'technical': 'sde_interviewer',
                'software': 'sde_interviewer',
                'engineering': 'sde_interviewer'
            }
            for key, personality in category_mapping.items():
                if key in job_category:
                    print(f"🎯 Personality detected from job_category: {personality} (job_category: {job_category})")
                    return personality
            print(f"⚠️ [DEBUG] No matching personality found for job_category: '{job_category}'")
    else:
        return "general_interviewer"
    
    try:
        # Initialize Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Create prompt for personality detection
        detection_prompt = f"""
Analyze the following interview questions and determine the most appropriate AI agent personality type.

QUESTIONS TO ANALYZE:
{questions_text}

AVAILABLE PERSONALITY TYPES:
1. corporate_interviewer - For business, finance, marketing, corporate roles, ROI analysis, budgeting
2. sde_interviewer - For general software engineering, programming, coding, algorithms, system design
3. python_expert - For Python-specific programming questions, libraries, frameworks
4. ai_ml_expert - For questions about AI, machine learning, NLP, deep learning, data science
5. dsa_expert - For data structures and algorithms, coding challenges, competitive programming
6. system_design_expert - For system design, architecture, scalability, distributed systems
7. general_interviewer - For mixed technical topics or general interview questions

INSTRUCTIONS:
- Analyze the content, topics, and themes in the questions
- Consider the overall context and purpose of the questions
- Choose the personality type that best matches the question content
- If questions cover multiple topics, choose the most dominant theme
- If uncertain or questions are very general, choose "general_interviewer"

Respond with ONLY the personality type name (e.g., "python_expert"), no explanations.
"""

        # Get LLM response
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing content and determining appropriate agent personalities. Always respond with only the personality type name."},
                {"role": "user", "content": detection_prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        detected_personality = response.choices[0].message.content.strip().lower()
        
        # Validate the detected personality is in our supported list
        valid_personalities = [
            "corporate_interviewer", "sde_interviewer", "python_expert", "ai_ml_expert", "dsa_expert", 
            "system_design_expert", "general_interviewer"
        ]
        
        if detected_personality in valid_personalities:
            print(f"🤖 LLM detected personality: {detected_personality}")
            return detected_personality
        else:
            print(f"⚠️ LLM returned unexpected personality '{detected_personality}', defaulting to general_interviewer")
            return "general_interviewer"
            
    except Exception as e:
        print(f"⚠️ Error in LLM personality detection: {e}")
        print("🔄 Falling back to keyword-based detection...")
        return detect_agent_personality_fallback(questions_mgr)
            
    except Exception as e:
        print(f"⚠️ Error in LLM personality detection: {e}")
        print("🔄 Falling back to keyword-based detection...")
        return detect_agent_personality_fallback(questions_mgr)

def detect_agent_personality_fallback(questions_mgr):
    """Fallback keyword-based personality detection if LLM fails"""
    if not questions_mgr:
        return "general_interviewer"
    
    # Handle both API and file-based question managers
    all_text = ""
    if hasattr(questions_mgr, 'get_current_questions'):
        # File-based manager
        questions = questions_mgr.get_current_questions()
        if not questions:
            return "general_interviewer"
        all_text = " ".join([q.text.lower() for q in questions])
        
    elif hasattr(questions_mgr, 'questions_data'):
        # API-based manager
        if not questions_mgr.questions_data or 'questions' not in questions_mgr.questions_data:
            return "general_interviewer"
        questions = questions_mgr.questions_data['questions']
        all_text = " ".join([q.get('text', q.get('question', '')).lower() for q in questions])
    else:
        return "general_interviewer"
    
    # Check for corporate/business content
    corporate_keywords = ['financial', 'finance', 'budget', 'roi', 'profit', 'loss', 'marketing', 'business', 'corporate', 'stakeholder', 'revenue', 'analytics', 'forecasting', 'planning']
    if any(keyword in all_text for keyword in corporate_keywords):
        return "corporate_interviewer"
    
    # Check for Python-specific content
    python_keywords = ['python', 'pandas', 'numpy', 'django', 'flask', 'list', 'tuple', 'dictionary']
    if any(keyword in all_text for keyword in python_keywords):
        return "python_expert"
    
    # Check for AI/ML content
    ai_keywords = ['nlp', 'machine learning', 'neural network', 'deep learning', 'bert', 'gpt', 'transformer']
    if any(keyword in all_text for keyword in ai_keywords):
        return "ai_ml_expert"
    
    # Check for DSA content
    dsa_keywords = ['algorithm', 'data structure', 'tree', 'graph', 'array', 'linked list', 'binary search', 'sorting']
    if any(keyword in all_text for keyword in dsa_keywords):
        return "dsa_expert"
    
    # Check for system design content
    system_keywords = ['system design', 'scalability', 'distributed', 'architecture', 'microservices', 'database design']
    if any(keyword in all_text for keyword in system_keywords):
        return "system_design_expert"
    
    # Check for general technical content
    tech_keywords = ['programming', 'coding', 'software', 'development', 'technical', 'engineering']
    if any(keyword in all_text for keyword in tech_keywords):
        return "sde_interviewer"
    
    # Default to general interviewer
    return "general_interviewer"

# Main personality detection function (now uses LLM by default)
def detect_agent_personality(questions_mgr):
    """Detect the appropriate agent personality based on question content using LLM"""
    print(f"🔧 [DEBUG] detect_agent_personality called with: {type(questions_mgr)}")
    result = detect_agent_personality_with_llm(questions_mgr)
    print(f"🔧 [DEBUG] detect_agent_personality_with_llm returned: '{result}'")
    return result

def get_agent_prompt(personality_type, questions_mgr):
    """Get the appropriate system prompt based on agent personality"""
    
    base_communication_rules = (
        "\n\nIMPORTANT: Your responses will be converted to speech. Use natural, conversational language without:"
        "\n- Asterisks (*) or any text formatting"
        "\n- Filler words (um, uh, well, basically, actually, like, you know)"
        "\n- Meta-commentary or stage directions"
        "\n- Parenthetical notes or asides"
        "\nSpeak directly to the person as if having a natural conversation."
    )
    
    if personality_type == "corporate_interviewer":
        agent_name = "Corporate Interviewer"
        base_prompt = (
            "You are a Corporate/Business Interviewer conducting a professional interview focused on business, finance, and corporate roles. "
            "Your goal is to assess the candidate's business acumen, analytical skills, and fit for corporate positions. "
            "\n\nYour Expertise:"
            "\n- Business strategy, financial planning, and analysis"
            "\n- Marketing, ROI analysis, and budget management"
            "\n- Corporate policies, compliance, and best practices"
            "\n- Cross-functional collaboration and stakeholder management"
            "\n- Data analysis, forecasting, and business intelligence"
            "\n\nInterview Style:"
            "\n- Professional and business-focused approach"
            "\n- Ask about real-world business scenarios and problem-solving"
            "\n- Discuss financial concepts, marketing strategies, and business operations"
            "\n- Evaluate analytical thinking and decision-making abilities"
            "\n- Focus on practical business applications and experience"
            "\n- Assess communication skills for stakeholder interactions"
        )
    
    elif personality_type == "python_expert":
        agent_name = "Python Expert"
        base_prompt = (
            "You are a Python programming expert conducting a technical interview focused on Python development. "
            "Your goal is to assess the candidate's Python knowledge, coding skills, and experience with Python frameworks. "
            "\n\nYour Expertise:"
            "\n- Deep knowledge of Python language features, syntax, and best practices"
            "\n- Experience with popular Python libraries (pandas, numpy, requests, etc.)"
            "\n- Understanding of Python frameworks like Django, Flask, FastAPI"
            "\n- Knowledge of Python testing, debugging, and optimization"
            "\n\nInterview Style:"
            "\n- Technical yet approachable when discussing Python concepts"
            "\n- Ask about Python-specific features, libraries, and frameworks"
            "\n- Discuss code quality, Pythonic ways of writing code"
            "\n- Provide coding challenges and ask for Python implementations"
        )
    
    elif personality_type == "sde_interviewer":
        agent_name = "SDE Interviewer"
        base_prompt = (
            "You are a Senior Software Development Engineer conducting a comprehensive technical interview. "
            "Your goal is to assess the candidate's technical skills, problem-solving abilities, and overall fit for software engineering roles. "
            "\n\nInterview Approach:"
            "\n- Create a welcoming, collaborative environment"
            "\n- Begin with introductions and background discussion"
            "\n- Progress through coding challenges, system design, and behavioral questions"
            "\n- Adapt difficulty based on candidate's experience level"
            "\n- Provide constructive feedback and guidance when needed"
            "\n- Allow adequate time for candidate questions"
            "\n\nCommunication Style:"
            "\n- Professional yet approachable and encouraging"
            "\n- Speak clearly and at a comfortable pace for voice interaction"
            "\n- Ask thoughtful follow-up questions to understand reasoning"
            "\n- Provide helpful hints without giving away answers"
            "\n- Summarize key points and provide clear next steps"
        )
    
    elif personality_type == "dsa_expert":
        agent_name = "DSA Expert"
        base_prompt = (
            "You are a Data Structures and Algorithms expert conducting a technical interview focused on DSA concepts. "
            "Your goal is to assess the candidate's understanding of algorithms, data structures, and problem-solving skills. "
            "\n\nYour Expertise:"
            "\n- Deep knowledge of data structures (arrays, trees, graphs, heaps, etc.)"
            "\n- Expert in algorithms (sorting, searching, dynamic programming, etc.)"
            "\n- Understanding of time and space complexity analysis"
            "\n- Experience with competitive programming and coding challenges"
            "\n\nInterview Style:"
            "\n- Focus on algorithmic thinking and problem-solving approach"
            "\n- Ask about data structure choices and trade-offs"
            "\n- Discuss time/space complexity of solutions"
            "\n- Provide coding challenges that test DSA knowledge"
        )
    
    elif personality_type == "system_design_expert":
        agent_name = "System Design Expert"
        base_prompt = (
            "You are a System Design expert conducting a technical interview focused on large-scale system architecture. "
            "Your goal is to assess the candidate's ability to design scalable, reliable, and efficient systems. "
            "\n\nYour Expertise:"
            "\n- Deep knowledge of distributed systems and scalability patterns"
            "\n- Experience with microservices, databases, and system architecture"
            "\n- Understanding of load balancing, caching, and performance optimization"
            "\n- Knowledge of cloud services and infrastructure design"
            "\n\nInterview Style:"
            "\n- Focus on high-level system architecture and design patterns"
            "\n- Ask about scalability, reliability, and performance considerations"
            "\n- Discuss trade-offs between different architectural choices"
            "\n- Guide through system design problems step by step"
        )
    
    elif personality_type == "ai_ml_expert":
        agent_name = "AI/ML Expert"
        base_prompt = (
            "You are an expert in Artificial Intelligence and Machine Learning conducting a technical interview focused on AI/ML concepts. "
            "Your goal is to assess the candidate's understanding of AI/ML algorithms, applications, and implementation. "
            "\n\nYour Expertise:"
            "\n- Deep knowledge of machine learning algorithms and techniques"
            "\n- Experience with neural networks, deep learning, and NLP"
            "\n- Understanding of data preprocessing, model training, and evaluation"
            "\n- Knowledge of AI/ML frameworks and tools (TensorFlow, PyTorch, etc.)"
            "\n\nInterview Style:"
            "\n- Technical yet accessible when discussing AI/ML concepts"
            "\n- Ask about algorithms, model selection, and implementation details"
            "\n- Discuss real-world applications and ethical considerations"
            "\n- Focus on both theoretical understanding and practical experience"
        )
    
    else:  # general_interviewer
        agent_name = "Interviewer"
        base_prompt = (
            "You are a friendly interviewer conducting an engaging conversation. "
            "You adapt your style to match the topics and questions you're discussing. "
            "\n\nYour Approach:"
            "\n- Be genuinely interested in the person's responses"
            "\n- Ask thoughtful follow-up questions"
            "\n- Keep the conversation natural and flowing"
            "\n- Adapt your tone to match the subject matter"
            "\n- Make the person feel comfortable and engaged"
        )
    
    # Add questions context if available
    if questions_mgr and questions_mgr.get_current_questions():
        summary = questions_mgr.get_questions_summary()
        questions_context = (
            f"\n\nSTRUCTURED QUESTIONS AVAILABLE:"
            f"\n- You have access to {summary['total']} pre-loaded questions"
            f"\n- Categories: {', '.join(summary['categories'].keys())}"
            f"\n- Follow the natural flow of conversation while using these specific questions"
            f"\n- When you receive a SUGGESTED NEXT QUESTION, use that as your primary question to ask"
        )
        full_prompt = base_prompt + questions_context + base_communication_rules + f"\n\nPlease start by introducing yourself as {agent_name} and begin the conversation."
    else:
        full_prompt = base_prompt + base_communication_rules + f"\n\nPlease start by introducing yourself as {agent_name} and begin the conversation."
    
    return full_prompt, agent_name

async def run():
    """Main function"""
    global agent
    try:
        print("Loading AI Agent...")
        
        # Setup questions before creating intelligence client
        questions_mgr = setup_questions()
        
        # Detect agent personality based on questions
        print(f"🔧 [DEBUG] About to detect personality for questions_mgr: {type(questions_mgr)}")
        personality_type = detect_agent_personality(questions_mgr)
        print(f"🔧 [DEBUG] Personality detection returned: '{personality_type}'")
        system_prompt, agent_name = get_agent_prompt(personality_type, questions_mgr)
        
        print(f"🎭 Agent Personality: {personality_type}")
        print(f"👤 Agent Name: {agent_name}")
        
        # audio player
        audio_track = CustomAudioStreamTrack(
            loop=loop,
            handle_interruption=True,
        )

        tts_client = DeepgramTTS(
            api_key=stt_api_key,
            output_track=audio_track,
        )
        
        # intelligence client with dynamic personality
        intelligence_client = GroqIntelligence( 
            api_key=llm_api_key, 
            model="openai/gpt-oss-120b", 
            tts=tts_client,
            system_prompt=system_prompt,
            questions_manager=questions_mgr,  # Pass questions manager to intelligence
            agent_name=agent_name  # Pass agent name for consistent labeling
        )

        # stt client
        stt_client = DeepgramSTT(
            loop=loop,
            api_key=stt_api_key,
            language=language,
            intelligence=intelligence_client
        )

        agent = AIInterviewer(
            loop=loop, 
            audio_track=audio_track, 
            stt=stt_client, 
            intelligence=intelligence_client,
            agent_name=agent_name,
            job_id=args.job_id if args else None,
            candidate_id=args.candidate_id if args else None
        )
       
        await agent.join(meeting_id=room_id, token=auth_token)

    except Exception as e:
        traceback.print_exc()
        print("Error while joining:", e)
    

async def destroy():
    """Delete character peer"""
    global agent
    global stopped
    print("Destroying AI Agent...")
    if agent is not None and not stopped:
        stopped = True
        await agent.leave()
        agent = None

def sigterm_handler(signum, frame):
    """Signal term handler"""
    print("EXITING with signal:", signum)
    # Schedule the destroy task and stop the loop gracefully
    if loop.is_running():
        # Schedule the cleanup task
        asyncio.create_task(destroy())
        # Stop the loop (but don't close it while running)
        loop.stop()
    else:
        # If loop is not running, we can clean up directly
        try:
            loop.run_until_complete(destroy())
            loop.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

def main():
    """Main entry point"""
    try:
        # Configure the logging module to capture logs from built-in modules and save to a file
        logging.basicConfig(
            filename='logfile.log',
            filemode='w', 
            level=logging.DEBUG
        )

        # Register the SIGTERM handler
        signal.signal(signal.SIGTERM, sigterm_handler)
        # Register the SIGINT handler
        signal.signal(signal.SIGINT, sigterm_handler)

        loop.run_until_complete(run())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Interrupted by user")
        # Handle KeyboardInterrupt gracefully
        if loop.is_running():
            loop.stop()
    finally:
        # Clean up resources
        try:
            if not loop.is_closed():
                loop.run_until_complete(destroy())
                loop.close()
        except Exception as e:
            print(f"Error during final cleanup: {e}")

if __name__ == "__main__":
    main()
