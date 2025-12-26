#!/usr/bin/env python3
"""
Simple test for Adaptive Interview Policy without external dependencies
This tests the core logic with simulated LLM analysis
"""

import os
import re
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

class SimpleAdaptivePolicy:
    """Simplified version with simulated LLM analysis for testing core logic"""
    
    def __init__(self):
        self.max_followups = 2
        self.followup_count = 0
    
    def analyze_response_simulated(self, question: str, response: str, category: str = "technical"):
        """Simulate LLM analysis based on response characteristics"""
        
        response_length = len(response.strip())
        response_lower = response.lower()
        
        # Simulate quality assessment based on response characteristics
        if response_length < 20:
            quality = "incomplete"
            followup_needed = "yes"
            reason = "Response too brief, needs elaboration"
            
        elif response_length < 50:
            quality = "poor"
            followup_needed = "yes"
            reason = "Very basic response, lacks detail and understanding"
            
        elif "time complexity" in question.lower() and ("o(1)" in response_lower or "o(n)" in response_lower or "o(log n)" in response_lower):
            quality = "good"
            followup_needed = "yes" if self.followup_count < self.max_followups else "no"
            reason = "Shows understanding of time complexity, could explore more"
            
        elif any(keyword in response_lower for keyword in ["lifo", "fifo", "stack", "queue", "binary search", "divide", "algorithm"]):
            if response_length > 200:
                quality = "excellent"
                followup_needed = "no"
                reason = "Comprehensive answer with technical details"
            else:
                quality = "good"
                followup_needed = "yes" if self.followup_count < self.max_followups else "no"
                reason = "Good technical understanding, could use more detail"
                
        elif any(keyword in response_lower for keyword in ["think", "maybe", "probably", "not sure"]):
            quality = "poor"
            followup_needed = "yes"
            reason = "Shows uncertainty, needs guidance"
            
        elif response_length > 100:
            quality = "partial"
            followup_needed = "yes" if self.followup_count < self.max_followups else "no"
            reason = "Decent length but missing key concepts"
            
        else:
            quality = "partial"
            followup_needed = "yes" if self.followup_count < self.max_followups else "no"
            reason = "Basic understanding, could be more comprehensive"
        
        return f"Quality: {quality}\nFollow-up needed: {followup_needed}\nReason: {reason}"
    
    def analyze_response(self, question: str, response: str, category: str = "technical"):
        """Use simulated analysis instead of external LLM"""
        return self.analyze_response_simulated(question, response, category)
    
    def decide_next_action(self, analysis: str):
        """Decide whether to ask follow-up or move to next question"""
        
        # Parse analysis
        quality = "partial"
        followup_needed = "yes"
        reason = ""
        
        lines = analysis.split('\n')
        for line in lines:
            if 'Quality:' in line:
                quality = line.split('Quality:')[1].strip().lower()
            elif 'Follow-up needed:' in line:
                followup_needed = line.split('Follow-up needed:')[1].strip().lower()
            elif 'Reason:' in line:
                reason = line.split('Reason:')[1].strip()
        
        # Decision logic based on quality and follow-up limits
        if quality == "excellent":
            action = "move_to_next"
            message = "🎉 Excellent response! You demonstrate strong understanding. Let's move to the next question."
            self.followup_count = 0  # Reset for next question
            
        elif quality == "good":
            if self.followup_count < self.max_followups and followup_needed == "yes":
                self.followup_count += 1
                action = "ask_followup"
                message = "👍 Good answer! Can you elaborate on one specific aspect or provide an example?"
            else:
                action = "move_to_next"
                message = "✅ Good response. Let's move to the next question."
                self.followup_count = 0  # Reset for next question
                
        elif quality == "partial":
            if self.followup_count < self.max_followups:
                self.followup_count += 1
                action = "ask_followup"
                message = "🤔 I see you have some understanding. Can you explain your approach in more detail?"
            else:
                action = "move_to_next"
                message = "📝 Thank you for your response. Let's try a different question."
                self.followup_count = 0  # Reset for next question
                
        elif quality == "poor":
            if self.followup_count < self.max_followups:
                self.followup_count += 1
                action = "ask_followup"
                message = "💡 Let me give you a hint: think about the core concepts step by step. What would be your first approach?"
            else:
                action = "move_to_next"
                message = "📚 No problem! Let's try a different type of question."
                self.followup_count = 0  # Reset for next question
                
        else:  # incomplete
            if self.followup_count < self.max_followups:
                self.followup_count += 1
                action = "ask_followup"
                message = "📋 Could you elaborate more on your answer? I'd like to understand your thinking process."
            else:
                action = "move_to_next"
                message = "⏭️ Let's move forward to the next question."
                self.followup_count = 0  # Reset for next question
        
        return action, message, reason

def test_simple_policy():
    """Test the simplified adaptive policy"""
    
    print("🧪 Testing Simplified Adaptive Policy (Simulated Analysis)\n")
    
    policy = SimpleAdaptivePolicy()
    
    # Test cases
    test_cases = [
        {
            "name": "Excellent Response",
            "question": "Explain the difference between a stack and a queue.",
            "response": "A stack is LIFO (Last-In-First-Out) where elements are added and removed from the top using push and pop operations. A queue is FIFO (First-In-First-Out) where elements are added at the rear (enqueue) and removed from the front (dequeue). Stacks are used for function call management, undo operations, and expression evaluation. Queues are used for breadth-first search, task scheduling, and handling requests in order. Both have O(1) time complexity for basic operations, but differ in their access patterns and use cases."
        },
        {
            "name": "Good Response", 
            "question": "How does binary search work?",
            "response": "Binary search works by repeatedly dividing the search space in half. You compare the target with the middle element and eliminate half the array each time. It requires a sorted array and has O(log n) time complexity."
        },
        {
            "name": "Partial Response",
            "question": "What is the time complexity of quicksort?",
            "response": "Quicksort divides the array around a pivot element and sorts the subarrays recursively."
        },
        {
            "name": "Poor Response",
            "question": "Explain how HTTP works.",
            "response": "I think HTTP is pretty fast, maybe."
        },
        {
            "name": "Incomplete Response",
            "question": "What is recursion?",
            "response": "It's when a function calls itself."
        }
    ]
    
    session_stats = {
        "questions_asked": 0,
        "followups_total": 0,
        "excellent_responses": 0,
        "moved_to_next": 0
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"=" * 60)
        print(f"TEST {i}: {test_case['name']}")
        print(f"=" * 60)
        print(f"Question: {test_case['question']}")
        print(f"Response: {test_case['response']}")
        print()
        
        session_stats["questions_asked"] += 1
        
        # Analyze response
        analysis = policy.analyze_response(
            test_case['question'], 
            test_case['response']
        )
        print(f"🔍 Analysis:")
        print(f"{analysis}")
        print()
        
        # Decide action
        action, message, reason = policy.decide_next_action(analysis)
        print(f"🎯 Decision: {action}")
        print(f"💬 AI Response: {message}")
        print(f"🧠 Reasoning: {reason}")
        
        # Update stats
        if action == "ask_followup":
            session_stats["followups_total"] += 1
        elif action == "move_to_next":
            session_stats["moved_to_next"] += 1
            
        if "excellent" in analysis.lower():
            session_stats["excellent_responses"] += 1
        
        print(f"📊 Current followup count for this question: {policy.followup_count}")
        print()
        
        # Simulate a follow-up if action is ask_followup
        if action == "ask_followup" and i <= 3:  # Only for first 3 tests
            print(f"🔄 Simulating follow-up scenario...")
            
            # Simulate candidate's follow-up response
            followup_responses = {
                1: "Additionally, stacks support push() and pop() operations, while queues support enqueue() and dequeue(). Memory allocation can also differ.",
                2: "The algorithm starts with the entire array, compares target with middle element, then recursively searches left or right half based on comparison.",
                3: "The average case is O(n log n) but worst case can be O(n²) if the pivot is always the smallest or largest element."
            }
            
            if i in followup_responses:
                followup_response = followup_responses[i]
                print(f"Candidate follow-up: {followup_response}")
                
                # Analyze follow-up
                followup_analysis = policy.analyze_response(test_case['question'], followup_response)
                followup_action, followup_message, followup_reason = policy.decide_next_action(followup_analysis)
                
                print(f"🔍 Follow-up Analysis: {followup_analysis.split('Reason:')[0].strip()}")
                print(f"🎯 Follow-up Decision: {followup_action}")
                print(f"💬 AI Follow-up Response: {followup_message}")
                print()
                
                if followup_action == "ask_followup":
                    session_stats["followups_total"] += 1
                elif followup_action == "move_to_next":
                    session_stats["moved_to_next"] += 1

if __name__ == "__main__":
    try:
        test_simple_policy()
        print("✅ Simple adaptive policy test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
