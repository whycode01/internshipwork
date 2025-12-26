#!/usr/bin/env python3
"""
Script to run the AI agent with different question sets
This demonstrates how to test different personas with their respective question types
"""

import os
import subprocess
import sys
from pathlib import Path

# Available question files and their expected personas
QUESTION_SETS = {
    "python": {
        "file": "questions/python_programming_questions.md",
        "description": "Python Programming Questions - Will trigger Python Expert persona",
        "expected_persona": "Python Expert",
        "topics": ["Python basics", "OOP", "Data structures", "Decorators", "Generators"]
    },
    "dsa": {
        "file": "questions/dsa_questions.md", 
        "description": "Data Structures & Algorithms - Will trigger DSA Expert persona",
        "expected_persona": "DSA Expert",
        "topics": ["Arrays", "Linked Lists", "Trees", "Algorithms", "Complexity Analysis"]
    },
    "nlp": {
        "file": "questions/NLP.md",
        "description": "Natural Language Processing - Will trigger AI/ML Expert persona", 
        "expected_persona": "AI/ML Expert",
        "topics": ["NLP Applications", "Transformers", "BERT", "GPT", "ML Techniques"]
    },
    "swe": {
        "file": "questions/swe_interview_questions.md",
        "description": "Software Engineering Interview - Will trigger SDE Interviewer persona",
        "expected_persona": "SDE Interviewer", 
        "topics": ["System Design", "Algorithms", "Data Structures", "General Programming"]
    }
}

def print_banner():
    """Print a nice banner"""
    print("=" * 70)
    print("🤖 AI AGENT QUESTION SET RUNNER")
    print("=" * 70)
    print("This script helps you run the AI agent with different question sets")
    print("Each question set will trigger a different agent persona automatically")
    print()

def list_available_questions():
    """List all available question sets"""
    print("📋 AVAILABLE QUESTION SETS:")
    print("-" * 40)
    
    for key, info in QUESTION_SETS.items():
        file_path = Path(info["file"])
        exists = "✅" if file_path.exists() else "❌"
        
        print(f"{exists} {key.upper()}")
        print(f"   📄 File: {info['file']}")
        print(f"   🎭 Persona: {info['expected_persona']}")
        print(f"   📝 Description: {info['description']}")
        print(f"   🏷️  Topics: {', '.join(info['topics'])}")
        print()

def run_agent_with_questions(question_set_key):
    """Run the AI agent with a specific question set"""
    if question_set_key not in QUESTION_SETS:
        print(f"❌ Error: Unknown question set '{question_set_key}'")
        print(f"Available sets: {', '.join(QUESTION_SETS.keys())}")
        return False
    
    question_info = QUESTION_SETS[question_set_key]
    question_file = question_info["file"]
    
    # Check if file exists
    if not Path(question_file).exists():
        print(f"❌ Error: Question file '{question_file}' not found!")
        return False
    
    print(f"🚀 Starting AI Agent with {question_set_key.upper()} questions...")
    print(f"📄 File: {question_file}")
    print(f"🎭 Expected Persona: {question_info['expected_persona']}")
    print(f"📝 Description: {question_info['description']}")
    print()
    print("⚡ Running command:")
    
    # Construct the command
    command = f'python main.py "{question_file}"'
    print(f"   {command}")
    print()
    print("Press Ctrl+C to stop the agent when done testing")
    print("=" * 50)
    
    try:
        # Run the main.py with the question file
        result = subprocess.run([sys.executable, "main.py", question_file], 
                              cwd=os.getcwd(),
                              check=True)
        return True
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def interactive_mode():
    """Interactive mode to select and run question sets"""
    while True:
        print_banner()
        list_available_questions()
        
        print("🎮 INTERACTIVE MODE")
        print("-" * 20)
        print("Enter the question set you want to test:")
        for key in QUESTION_SETS.keys():
            print(f"  • {key}")
        print("  • 'list' - Show available question sets again")
        print("  • 'quit' or 'exit' - Exit the program")
        print()
        
        choice = input("Your choice: ").strip().lower()
        
        if choice in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        elif choice == 'list':
            continue
        elif choice in QUESTION_SETS:
            print()
            success = run_agent_with_questions(choice)
            if success:
                print("\n✅ Agent session completed")
            else:
                print("\n❌ Agent session failed")
            
            input("\nPress Enter to continue...")
        else:
            print(f"❌ Invalid choice: '{choice}'")
            input("Press Enter to try again...")

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # No arguments - run interactive mode
        interactive_mode()
    elif len(sys.argv) == 2:
        question_set = sys.argv[1].lower()
        if question_set in ['--help', '-h', 'help']:
            print_usage()
        elif question_set == '--list':
            print_banner()
            list_available_questions()
        else:
            # Run with specific question set
            success = run_agent_with_questions(question_set)
            sys.exit(0 if success else 1)
    else:
        print("❌ Too many arguments")
        print_usage()
        sys.exit(1)

def print_usage():
    """Print usage information"""
    print_banner()
    print("📖 USAGE:")
    print("   python run_with_questions.py                 # Interactive mode")
    print("   python run_with_questions.py <question_set>  # Run specific set")
    print("   python run_with_questions.py --list          # List available sets")
    print("   python run_with_questions.py --help          # Show this help")
    print()
    print("📋 Available question sets:")
    for key, info in QUESTION_SETS.items():
        print(f"   • {key} - {info['expected_persona']}")
    print()
    print("💡 EXAMPLES:")
    print("   python run_with_questions.py python          # Run with Python questions")
    print("   python run_with_questions.py dsa             # Run with DSA questions") 
    print("   python run_with_questions.py nlp             # Run with NLP questions")
    print("   python run_with_questions.py swe             # Run with SWE questions")

if __name__ == "__main__":
    main()
