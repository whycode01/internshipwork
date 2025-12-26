#!/usr/bin/env python3
"""
Test script for transcript system
"""

import time

from transcript.transcript_manager import TranscriptManager


def test_transcript_system():
    print("🧪 Testing transcript system...")
    
    # Initialize transcript manager
    tm = TranscriptManager()
    print("✅ TranscriptManager initialized")
    
    # Start recording
    interview_id = tm.start_recording('test-meeting-123', ['AI Agent', 'Test Candidate'])
    print(f"✅ Started recording with interview ID: {interview_id}")
    
    # Add sample entries
    tm.add_entry('AI Agent', 'Hello! Let\'s begin the interview.', message_type='speech')
    tm.add_entry('Test Candidate', 'Hi there! I\'m ready to start.', message_type='speech')
    tm.add_entry('AI Agent', 'Great! Can you tell me about your experience?', message_type='speech')
    tm.add_entry('Test Candidate', 'I have 3 years of experience in Python development.', message_type='speech')
    print("✅ Added sample conversation entries")
    
    # Test current transcript text
    current_text = tm.get_current_transcript_text()
    print("✅ Generated current transcript text")
    print("📝 Sample transcript preview:")
    print("-" * 50)
    print(current_text[:200] + "..." if len(current_text) > 200 else current_text)
    print("-" * 50)
    
    # End recording
    filename = tm.end_recording()
    print(f"✅ Recording ended, saved as: {filename}")
    
    # List transcripts
    transcripts = tm.list_transcripts()
    print(f"✅ Found {len(transcripts)} transcript files:")
    for transcript in transcripts[:3]:  # Show first 3
        print(f"   - {transcript}")
    
    print("🎉 Transcript system test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_transcript_system()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()