#!/usr/bin/env python3
"""
Test script to verify persona detection consistency and prevent conflicts
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (detect_agent_personality_fallback,
                  detect_agent_personality_with_llm, get_agent_prompt)


def test_persona_detection():
    """Test persona detection with various question sets"""
    
    # Test cases with expected personas
    test_cases = [
        {
            "description": "Python-focused questions",
            "questions": [
                "What is the difference between list and tuple in Python?",
                "Explain Python decorators and how to use them",
                "How do you handle exceptions in Python?",
                "What are Python generators and when would you use them?"
            ],
            "expected_fallback": "python_expert"
        },
        {
            "description": "AI/ML focused questions",
            "questions": [
                "Explain the difference between supervised and unsupervised learning",
                "What is a neural network and how does it work?",
                "Describe the transformer architecture used in BERT and GPT",
                "How do you handle overfitting in machine learning models?"
            ],
            "expected_fallback": "ai_ml_expert"
        },
        {
            "description": "DSA focused questions",
            "questions": [
                "Explain the time complexity of binary search",
                "How would you implement a binary tree traversal?",
                "What is the difference between BFS and DFS algorithms?",
                "Describe dynamic programming and give an example"
            ],
            "expected_fallback": "dsa_expert"
        },
        {
            "description": "System Design focused questions",
            "questions": [
                "How would you design a scalable messaging system?",
                "Explain microservices architecture and its benefits",
                "How do you handle load balancing in distributed systems?",
                "Design a database schema for a social media platform"
            ],
            "expected_fallback": "system_design_expert"
        },
        {
            "description": "General SDE questions",
            "questions": [
                "What is your experience with software development?",
                "How do you approach debugging complex issues?",
                "Describe your coding workflow and best practices",
                "What programming languages are you comfortable with?"
            ],
            "expected_fallback": "sde_interviewer"
        },
        {
            "description": "Mixed/General questions",
            "questions": [
                "Tell me about yourself",
                "What are your strengths and weaknesses?",
                "Where do you see yourself in 5 years?",
                "Why are you interested in this position?"
            ],
            "expected_fallback": "general_interviewer"
        }
    ]
    
    print("🧪 Testing Persona Detection Consistency")
    print("=" * 50)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print("-" * 30)
        
        # Create a temporary question manager with test questions
        class MockQuestion:
            def __init__(self, text):
                self.text = text
                
        class MockQuestionManager:
            def __init__(self, questions):
                self.questions = [MockQuestion(q) for q in questions]
                
            def get_current_questions(self):
                return self.questions
                
            def get_questions_summary(self):
                return {
                    'total': len(self.questions),
                    'categories': {'test': len(self.questions)}
                }
        
        mock_mgr = MockQuestionManager(test_case['questions'])
        
        # Test fallback detection (keyword-based)
        fallback_result = detect_agent_personality_fallback(mock_mgr)
        print(f"🔍 Fallback Detection: {fallback_result}")
        print(f"✅ Expected: {test_case['expected_fallback']}")
        print(f"{'✅ PASS' if fallback_result == test_case['expected_fallback'] else '❌ FAIL'}")
        
        # Test if we can get the agent prompt without errors
        try:
            prompt, agent_name = get_agent_prompt(fallback_result, mock_mgr)
            print(f"👤 Agent Name: {agent_name}")
            print(f"📝 Prompt Length: {len(prompt)} characters")
            
            # Check that agent name is consistent with personality
            expected_names = {
                "python_expert": "Python Expert",
                "ai_ml_expert": "AI/ML Expert", 
                "dsa_expert": "DSA Expert",
                "system_design_expert": "System Design Expert",
                "sde_interviewer": "SDE Interviewer",
                "general_interviewer": "Interviewer"
            }
            
            expected_name = expected_names.get(fallback_result, "Unknown")
            name_match = agent_name == expected_name
            print(f"🏷️  Name Consistency: {'✅ PASS' if name_match else '❌ FAIL'}")
            
            results.append({
                'test': test_case['description'],
                'detection_correct': fallback_result == test_case['expected_fallback'],
                'name_consistent': name_match,
                'detected_persona': fallback_result,
                'agent_name': agent_name
            })
            
        except Exception as e:
            print(f"❌ Error getting prompt: {e}")
            results.append({
                'test': test_case['description'],
                'detection_correct': False,
                'name_consistent': False,
                'detected_persona': fallback_result,
                'agent_name': 'ERROR',
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY RESULTS")
    print("=" * 50)
    
    passed_detection = sum(1 for r in results if r['detection_correct'])
    passed_naming = sum(1 for r in results if r['name_consistent'])
    total_tests = len(results)
    
    print(f"🎯 Detection Accuracy: {passed_detection}/{total_tests} ({passed_detection/total_tests*100:.1f}%)")
    print(f"🏷️  Naming Consistency: {passed_naming}/{total_tests} ({passed_naming/total_tests*100:.1f}%)")
    
    if passed_detection == total_tests and passed_naming == total_tests:
        print("\n✅ ALL TESTS PASSED - Persona detection is working correctly!")
        print("🔒 No conflicts detected - each question set maps to exactly one persona")
    else:
        print("\n⚠️  Some tests failed - review persona detection logic")
        for result in results:
            if not result['detection_correct'] or not result['name_consistent']:
                print(f"   ❌ {result['test']}: {result['detected_persona']} -> {result['agent_name']}")
    
    return results

def test_consistency_single_session():
    """Test that a single session maintains consistent persona"""
    print("\n🔒 Testing Single Session Consistency")
    print("=" * 50)
    
    # Simulate questions that might appear in a single interview
    mixed_questions = [
        "Tell me about your Python experience",  # Could trigger python_expert
        "Explain object-oriented programming",   # Could trigger sde_interviewer  
        "What is your background?",              # Could trigger general_interviewer
    ]
    
    class MockQuestion:
        def __init__(self, text):
            self.text = text
            
    class MockQuestionManager:
        def __init__(self, questions):
            self.questions = [MockQuestion(q) for q in questions]
            
        def get_current_questions(self):
            return self.questions
            
        def get_questions_summary(self):
            return {
                'total': len(self.questions),
                'categories': {'mixed': len(self.questions)}
            }
    
    mock_mgr = MockQuestionManager(mixed_questions)
    
    # Test that detection is consistent across multiple calls
    results = []
    for i in range(5):
        persona = detect_agent_personality_fallback(mock_mgr)
        results.append(persona)
        print(f"🔄 Call {i+1}: {persona}")
    
    # Check consistency
    unique_personas = set(results)
    if len(unique_personas) == 1:
        print(f"✅ CONSISTENT: All calls returned '{results[0]}'")
        return True
    else:
        print(f"❌ INCONSISTENT: Got different personas: {unique_personas}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Persona Detection Tests")
    
    # Test persona detection accuracy
    detection_results = test_persona_detection()
    
    # Test single session consistency  
    consistency_result = test_consistency_single_session()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    
    if all(r['detection_correct'] and r['name_consistent'] for r in detection_results) and consistency_result:
        print("✅ ALL TESTS PASSED")
        print("🎯 Persona detection is accurate and consistent")
        print("🔒 No conflicts detected in dynamic persona selection")
        exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Review persona detection logic for potential conflicts")
        exit(1)
