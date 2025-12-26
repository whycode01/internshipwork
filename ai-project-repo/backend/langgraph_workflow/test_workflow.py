#!/usr/bin/env python3
"""
Test script for the LangGraph interview assessment workflow.
Simulates a complete workflow run with sample data.
"""

import asyncio
import json

from workflow import InterviewAssessmentWorkflow

# Sample test data from the attached file
TEST_DATA = {
    "candidate_id": "test_candidate_001",
    "candidate_name": "John Doe",
    "raw_transcript": "Interviewer: Good morning John, thank you for joining us today. Can you start by telling us about your background and experience with Python development?\n\nJohn: Good morning! Thank you for having me. I've been working as a Python developer for about 4 years now. I started my career at a small startup where I worked on web applications using Django and Flask. In my current role at TechCorp, I've been focusing on building APIs and microservices using FastAPI.",
    "resume_text": "John Doe\nSenior Python Developer\nEmail: john.doe@email.com\n4+ years Python development experience",
    "job_description": {
        "title": "Senior Python Developer",
        "department": "Engineering",
        "experience_required": "3-5 years",
        "technical_requirements": [
            "Strong Python programming skills",
            "Experience with web frameworks (Django, Flask, FastAPI)",
            "Database experience (PostgreSQL, MongoDB)"
        ]
    },
    "policy_template": {
        "name": "Senior Python Developer Assessment Policy",
        "assessment_criteria": {
            "technical_skills": {
                "weight": 35,
                "subcriteria": ["Python programming proficiency", "Framework knowledge"]
            },
            "behavioral_competencies": {
                "weight": 25,
                "subcriteria": ["Communication clarity", "Problem-solving approach"]
            },
            "experience_relevance": {
                "weight": 25,
                "subcriteria": ["Years of relevant experience", "Technology stack alignment"]
            },
            "cultural_fit": {
                "weight": 15,
                "subcriteria": ["Company values alignment", "Growth mindset"]
            }
        }
    }
}

class MockRequest:
    """Mock request object for testing."""
    def __init__(self):
        self.app = MockApp()
        
class MockApp:
    """Mock FastAPI app for testing."""
    def __init__(self):
        self.state = MockState()
        
class MockState:
    """Mock app state for testing."""
    def __init__(self):
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=4)

async def test_workflow():
    """Test the complete workflow execution."""
    print("🚀 Starting LangGraph Interview Assessment Workflow Test")
    print("=" * 60)
    
    try:
        # Create workflow instance
        workflow = InterviewAssessmentWorkflow()
        print("✅ Workflow initialized successfully")
        
        # Create mock request
        mock_request = MockRequest()
        print("✅ Mock request created")
        
        # Run the assessment
        print("🔄 Running assessment workflow...")
        result = await workflow.run_assessment(TEST_DATA, mock_request)
        
        print("\n📊 ASSESSMENT RESULTS")
        print("=" * 60)
        print(f"Candidate: {result.get('candidate_name')}")
        print(f"Technical Score: {result.get('technical_score', 'N/A')}")
        print(f"Behavioral Score: {result.get('behavioral_score', 'N/A')}")
        print(f"Experience Score: {result.get('experience_score', 'N/A')}")
        print(f"Cultural Score: {result.get('cultural_score', 'N/A')}")
        print(f"Final Score: {result.get('final_score', 'N/A')}")
        print(f"Decision: {result.get('decision', 'N/A')}")
        print(f"Quality Check: {'✅ PASSED' if result.get('quality_check_passed') else '❌ FAILED'}")
        
        if result.get('generated_report'):
            print(f"\n📋 Report Length: {len(result.get('generated_report', ''))} characters")
        
        if result.get('processing_errors'):
            print(f"\n⚠️  Processing Errors: {len(result.get('processing_errors', []))}")
            for error in result.get('processing_errors', []):
                print(f"  - {error}")
        
        print("\n✅ Workflow test completed successfully!")
        return result
        
    except Exception as e:
        print(f"\n❌ Workflow test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("LangGraph Interview Assessment Workflow - Test Runner")
    print("Note: This test requires proper LLM configuration and database setup")
    print("\nStarting test in 3 seconds...")
    
    import time
    time.sleep(3)
    
    # Run the test
    result = asyncio.run(test_workflow())
    
    if result:
        print(f"\n🎉 Test completed! Final score: {result.get('final_score', 'N/A')}")
    else:
        print("\n💥 Test failed - check logs above for details")