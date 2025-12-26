#!/usr/bin/env python3
"""
Test script for organized transcript system with job_id and candidate_id
"""

import json
import time

import requests

BASE_URL = "http://localhost:8001"

def test_organized_transcript_system():
    """Test the organized transcript system with job and candidate IDs"""
    
    print("🧪 Testing Organized Transcript System")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            "meeting_id": "meeting-001",
            "job_id": "job-001",
            "candidate_id": "candidate-alice",
            "participants": ["AI Interviewer", "Alice Johnson"]
        },
        {
            "meeting_id": "meeting-002", 
            "job_id": "job-001",
            "candidate_id": "candidate-bob",
            "participants": ["AI Interviewer", "Bob Smith"]
        },
        {
            "meeting_id": "meeting-003",
            "job_id": "job-002", 
            "candidate_id": "candidate-charlie",
            "participants": ["AI Interviewer", "Charlie Wilson"]
        }
    ]
    
    # Test 1: Start transcript recordings with job/candidate info
    print("\n📝 Test 1: Starting transcript recordings with job/candidate info")
    for i, test_case in enumerate(test_cases):
        print(f"\n   Creating transcript {i+1}:")
        print(f"   📋 Meeting: {test_case['meeting_id']}")
        print(f"   💼 Job: {test_case['job_id']}")
        print(f"   👤 Candidate: {test_case['candidate_id']}")
        
        # Start recording
        response = requests.post(f"{BASE_URL}/transcripts/start", params={
            "meeting_id": test_case["meeting_id"],
            "job_id": test_case["job_id"],
            "candidate_id": test_case["candidate_id"],
            "participants": test_case["participants"]
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Started recording: {result['interview_id']}")
        else:
            print(f"   ❌ Failed to start: {response.text}")
            continue
        
        # Add some sample entries (simulated conversation)
        sample_entries = [
            ("AI Interviewer", f"Hello! Let's start the interview for {test_case['job_id']}"),
            (test_case['participants'][1].split()[0], "Thank you, I'm ready to begin."),
            ("AI Interviewer", "Can you tell me about your background?"),
            (test_case['participants'][1].split()[0], "I have 5 years of experience in software development...")
        ]
        
        # Stop recording to save the transcript
        time.sleep(1)  # Small delay to simulate conversation
        stop_response = requests.post(f"{BASE_URL}/transcripts/stop")
        if stop_response.status_code == 200:
            print(f"   ✅ Recording stopped and saved")
        else:
            print(f"   ⚠️ Failed to stop recording: {stop_response.text}")
    
    print("\n" + "="*50)
    
    # Test 2: List all transcripts
    print("\n📋 Test 2: Listing all transcripts")
    response = requests.get(f"{BASE_URL}/transcripts/")
    if response.status_code == 200:
        transcripts = response.json()["transcripts"]
        print(f"   📊 Total transcripts: {len(transcripts)}")
        for transcript in transcripts:
            print(f"   📄 {transcript['filename']} - Meeting: {transcript.get('meeting_id', 'N/A')}")
    else:
        print(f"   ❌ Failed to list transcripts: {response.text}")
    
    # Test 3: Filter by job_id
    print("\n🔍 Test 3: Filtering transcripts by job_id")
    for job_id in ["job-001", "job-002"]:
        response = requests.get(f"{BASE_URL}/transcripts/", params={"job_id": job_id})
        if response.status_code == 200:
            transcripts = response.json()["transcripts"]
            print(f"   💼 Job {job_id}: {len(transcripts)} transcripts")
            for transcript in transcripts:
                print(f"      📄 {transcript['filename']}")
        else:
            print(f"   ❌ Failed to filter by job {job_id}: {response.text}")
    
    # Test 4: Filter by candidate_id
    print("\n👤 Test 4: Filtering transcripts by candidate_id")
    for candidate_id in ["candidate-alice", "candidate-bob"]:
        response = requests.get(f"{BASE_URL}/transcripts/", params={"candidate_id": candidate_id})
        if response.status_code == 200:
            transcripts = response.json()["transcripts"]
            print(f"   👤 Candidate {candidate_id}: {len(transcripts)} transcripts")
            for transcript in transcripts:
                print(f"      📄 {transcript['filename']}")
        else:
            print(f"   ❌ Failed to filter by candidate {candidate_id}: {response.text}")
    
    # Test 5: Get transcripts by specific job
    print("\n🎯 Test 5: Getting transcripts by specific job endpoint")
    response = requests.get(f"{BASE_URL}/transcripts/job/job-001")
    if response.status_code == 200:
        transcripts = response.json()["transcripts"]
        print(f"   💼 Job job-001: {len(transcripts)} transcripts")
        for transcript in transcripts:
            print(f"      📄 {transcript['filename']} - Meeting: {transcript.get('meeting_id', 'N/A')}")
    else:
        print(f"   ❌ Failed to get transcripts for job-001: {response.text}")
    
    # Test 6: Get transcripts by specific candidate
    print("\n👤 Test 6: Getting transcripts by specific candidate endpoint")
    response = requests.get(f"{BASE_URL}/transcripts/candidate/candidate-alice")
    if response.status_code == 200:
        transcripts = response.json()["transcripts"]
        print(f"   👤 Candidate candidate-alice: {len(transcripts)} transcripts")
        for transcript in transcripts:
            print(f"      📄 {transcript['filename']} - Meeting: {transcript.get('meeting_id', 'N/A')}")
    else:
        print(f"   ❌ Failed to get transcripts for candidate-alice: {response.text}")
    
    # Test 7: Get transcripts by job and candidate combination
    print("\n🎯👤 Test 7: Getting transcripts by job and candidate combination")
    response = requests.get(f"{BASE_URL}/transcripts/job/job-001/candidate/candidate-alice")
    if response.status_code == 200:
        transcripts = response.json()["transcripts"]
        print(f"   🎯👤 Job job-001 + Candidate candidate-alice: {len(transcripts)} transcripts")
        for transcript in transcripts:
            print(f"      📄 {transcript['filename']} - Meeting: {transcript.get('meeting_id', 'N/A')}")
    else:
        print(f"   ❌ Failed to get transcripts for job-001 + candidate-alice: {response.text}")
    
    print("\n" + "="*50)
    print("✅ Organized transcript system test completed!")
    print("\n💡 Benefits for Audit AI integration:")
    print("   - Transcripts organized by job_id/candidate_id structure")
    print("   - Multiple filtering endpoints for efficient retrieval")
    print("   - Hierarchical storage: transcripts/job-X/candidate-Y/")
    print("   - API endpoints ready for external audit AI app integration")
    print("   - Port separation: VideoSDK (8001) vs Audit AI (8000)")

if __name__ == "__main__":
    try:
        test_organized_transcript_system()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to transcript API server.")
        print("💡 Make sure the server is running: python api_server.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")