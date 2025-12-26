#!/usr/bin/env python3
"""
Test script for Adaptive Interview Policy using LangGraph

This script demonstrates how the adaptive policy works:
1. Analyzes candidate responses 
2. Decides whether to ask follow-up or move to next question
3. Adapts difficulty based on performance
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

from intelligence.adaptive_policy import InterviewFlowManager

load_dotenv()

def test_adaptive_policy():
    """Test the adaptive interview policy with sample responses"""
    
    # Initialize the flow manager
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        return
    
    flow_manager = InterviewFlowManager(groq_api_key)
    
    # Simulate an interview scenario
    print("🚀 Testing Adaptive Interview Policy with LangGraph\n")
    
    # Test Case 1: Excellent Response
    print("=" * 60)
    print("TEST CASE 1: Excellent Technical Response")
    print("=" * 60)
    
    question1 = "Explain the difference between a stack and a queue data structure."
    response1 = """A stack is a Last-In-First-Out (LIFO) data structure where elements are added and removed from the same end, called the top. Common operations are push (add) and pop (remove). A queue is a First-In-First-Out (FIFO) data structure where elements are added at the rear and removed from the front. Common operations are enqueue (add) and dequeue (remove). 

Stacks are useful for function call management, undo operations, and expression evaluation. Queues are useful for breadth-first search, handling requests in order, and scheduling tasks. The time complexity for basic operations in both is O(1)."""
    
    result1 = flow_manager.process_response(
        current_question=question1,
        candidate_response=response1,
        candidate_name="John Doe",
        question_category="data_structures",
        question_difficulty="medium"
    )
    
    print(f"📊 Analysis Quality: {result1['analysis'].get('quality', 'N/A')}")
    print(f"🎯 Decision: {result1['action']}")
    print(f"💡 Explanation: {result1['explanation']}")
    print(f"🗣️ AI Response: {result1['response']}")
    print()
    
    # Test Case 2: Partial Response
    print("=" * 60)
    print("TEST CASE 2: Partial Understanding")
    print("=" * 60)
    
    question2 = "How would you implement a binary search algorithm?"
    response2 = "Binary search works by repeatedly dividing the search space in half. You compare the target with the middle element and eliminate half the array each time."
    
    result2 = flow_manager.process_response(
        current_question=question2,
        candidate_response=response2,
        candidate_name="Jane Smith",
        question_category="algorithms",
        question_difficulty="medium"
    )
    
    print(f"📊 Analysis Quality: {result2['analysis'].get('quality', 'N/A')}")
    print(f"🎯 Decision: {result2['action']}")
    print(f"💡 Explanation: {result2['explanation']}")
    print(f"🗣️ AI Response: {result2['response']}")
    print()
    
    # Test Case 3: Poor Response
    print("=" * 60)
    print("TEST CASE 3: Poor Understanding")
    print("=" * 60)
    
    question3 = "What is the time complexity of quicksort?"
    response3 = "I think it's pretty fast, maybe linear time?"
    
    result3 = flow_manager.process_response(
        current_question=question3,
        candidate_response=response3,
        candidate_name="Bob Wilson",
        question_category="algorithms",
        question_difficulty="medium"
    )
    
    print(f"📊 Analysis Quality: {result3['analysis'].get('quality', 'N/A')}")
    print(f"🎯 Decision: {result3['action']}")
    print(f"💡 Explanation: {result3['explanation']}")
    print(f"🗣️ AI Response: {result3['response']}")
    print()
    
    # Test Case 4: Incomplete Response
    print("=" * 60)
    print("TEST CASE 4: Incomplete Response")
    print("=" * 60)
    
    question4 = "Explain how HTTP works."
    response4 = "HTTP is a protocol."
    
    result4 = flow_manager.process_response(
        current_question=question4,
        candidate_response=response4,
        candidate_name="Alice Brown",
        question_category="networking",
        question_difficulty="easy"
    )
    
    print(f"📊 Analysis Quality: {result4['analysis'].get('quality', 'N/A')}")
    print(f"🎯 Decision: {result4['action']}")
    print(f"💡 Explanation: {result4['explanation']}")
    print(f"🗣️ AI Response: {result4['response']}")
    print()
    
    # Show session statistics
    print("=" * 60)
    print("SESSION STATISTICS")
    print("=" * 60)
    stats = flow_manager.get_session_stats()
    for key, value in stats.items():
        print(f"📈 {key.replace('_', ' ').title()}: {value}")

def test_follow_up_scenarios():
    """Test multiple follow-up scenarios"""
    
    print("\n🔄 Testing Follow-up Question Scenarios\n")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    flow_manager = InterviewFlowManager(groq_api_key)
    
    # Simulate a question that gets multiple follow-ups
    question = "How would you design a URL shortener like bit.ly?"
    
    # First response - partial
    response1 = "I would use a database to store the mappings between short and long URLs."
    
    result1 = flow_manager.process_response(
        current_question=question,
        candidate_response=response1,
        candidate_name="Sarah",
        question_category="system_design",
        question_difficulty="hard"
    )
    
    print(f"Round 1 - Decision: {result1['action']}")
    print(f"Follow-up: {result1['response']}\n")
    
    # Second response - still partial, should get another follow-up
    response2 = "I would use a hash function to generate the short codes and use a NoSQL database for better performance."
    
    result2 = flow_manager.process_response(
        current_question=question,
        candidate_response=response2,
        candidate_name="Sarah",
        question_category="system_design", 
        question_difficulty="hard"
    )
    
    print(f"Round 2 - Decision: {result2['action']}")
    print(f"Follow-up: {result2['response']}\n")
    
    # Third response - should hit follow-up limit
    response3 = "I would also need to consider caching for frequently accessed URLs."
    
    result3 = flow_manager.process_response(
        current_question=question,
        candidate_response=response3,
        candidate_name="Sarah",
        question_category="system_design",
        question_difficulty="hard"
    )
    
    print(f"Round 3 - Decision: {result3['action']}")
    print(f"Response: {result3['response']}\n")

if __name__ == "__main__":
    print("🎓 Adaptive Interview Policy Test Suite\n")
    
    try:
        test_adaptive_policy()
        test_follow_up_scenarios()
        
        print("\n🎉 All tests completed successfully!")
        print("\n💡 Key Features Demonstrated:")
        print("   ✅ Intelligent response analysis using LLM")
        print("   ✅ Adaptive decision making with LangGraph")
        print("   ✅ Follow-up question generation")
        print("   ✅ Interview flow management")
        print("   ✅ Time and follow-up limits")
        print("   ✅ Quality-based progression")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
