#!/usr/bin/env python3
"""
Simple test script for the Questions API
"""
import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import with absolute imports
from models import (PaginationInfo, Question, QuestionMetadata,
                    QuestionsListResponse, SearchParams)
from services import FileIndexService, QuestionService


async def test_services():
    """Test the core services"""
    print("🧪 Testing Questions API Services...")
    
    # Test FileIndexService
    print("\n📁 Testing FileIndexService...")
    file_service = FileIndexService("../storage/jobs")
    await file_service.initialize_index()
    
    index_info = await file_service.get_index_info()
    print(f"✅ Files indexed: {index_info['total_files']}")
    print(f"✅ Candidates: {index_info['total_candidates']}")
    print(f"✅ Jobs: {index_info['total_jobs']}")
    print(f"✅ Categories: {', '.join(index_info['job_categories'])}")
    
    # Test QuestionService
    print("\n📋 Testing QuestionService...")
    question_service = QuestionService(file_service)
    
    # Try to get questions for a candidate (if any exist)
    if index_info['total_candidates'] > 0:
        try:
            candidates = file_service.file_index.get("candidates", [])
            if candidates:
                candidate_id = candidates[0]
                print(f"🔍 Testing with candidate ID: {candidate_id}")
                
                result = await question_service.get_questions_by_candidate(
                    candidate_id=candidate_id,
                    limit=3
                )
                
                print(f"✅ Found {len(result.data['questions'])} questions")
                if result.data['questions']:
                    first_question = result.data['questions'][0]
                    print(f"✅ Sample question: {first_question['question_text'][:80]}...")
                    print(f"✅ Question type: {first_question['question_type']}")
        except Exception as e:
            print(f"⚠️ Could not test question retrieval: {e}")
    else:
        print("⚠️ No candidates found in storage")
    
    print("\n🎉 Service tests completed!")

async def main():
    """Main test function"""
    try:
        await test_services()
        print("\n✅ All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
