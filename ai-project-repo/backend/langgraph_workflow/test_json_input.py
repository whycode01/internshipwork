#!/usr/bin/env python3
"""
Test script for running the LangGraph workflow with test_input.json data.
This simulates how LangGraph Studio would run the workflow.
"""

import asyncio
import json

from workflow import InterviewAssessmentWorkflow


async def test_with_json_input():
    """Test the workflow with the test_input.json data."""
    print("🚀 Testing LangGraph Workflow with test_input.json")
    print("=" * 60)
    
    try:
        # Load test data from JSON file
        with open('test_input.json', 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        print("✅ Test data loaded from test_input.json")
        
        # Create workflow instance
        workflow = InterviewAssessmentWorkflow()
        print("✅ Workflow initialized successfully")
        
        # Run the assessment with None request (simulating LangGraph Studio)
        print("🔄 Running assessment workflow with None request...")
        result = await workflow.run_assessment(test_data, request=None)
        
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
        
        processing_errors = result.get('processing_errors', [])
        if processing_errors:
            print(f"\n⚠️  Processing Errors ({len(processing_errors)}):")
            for i, error in enumerate(processing_errors):
                print(f"{i} {error[:50]}... {error}")
        else:
            print("\n✅ No processing errors!")
        
        print("\n✅ Workflow test completed successfully!")
        return result
        
    except Exception as e:
        print(f"\n❌ Workflow test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("LangGraph Workflow Test - JSON Input")
    print("Testing with None request object (LangGraph Studio simulation)")
    
    # Run the test
    result = asyncio.run(test_with_json_input())
    
    if result:
        print(f"\n🎉 Test completed! Final score: {result.get('final_score', 'N/A')}")
    else:
        print("\n💥 Test failed - check logs above for details")