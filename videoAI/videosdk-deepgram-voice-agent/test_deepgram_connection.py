#!/usr/bin/env python3
"""
Simple test to verify Deepgram API connection
"""

import os

from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions


def test_deepgram_connection():
    """Test basic Deepgram connection"""
    
    # Load API key
    api_key = "0c750f535fcae3a62a3778f40ee0a309f81226df"
    
    if not api_key:
        print("❌ No Deepgram API key found")
        return False
    
    print(f"🔧 Testing Deepgram connection with key: {api_key[:10]}...")
    
    try:
        # Initialize client
        client = DeepgramClient(api_key=api_key)
        print("✅ Deepgram client created successfully")
        
        # Test with minimal live options
        minimal_options = LiveOptions(
            model="nova-2",
            language="en-US",
            encoding="linear16",
            sample_rate=48000,
            interim_results=True
        )
        
        print("🔧 Testing live transcription connection...")
        connection = client.listen.live.v("1")
        
        # Try to start connection (this will test authentication)
        result = connection.start(minimal_options)
        print(f"📊 Connection start result: {result}")
        
        if result:
            print("✅ Live transcription connection successful!")
            connection.finish()
            return True
        else:
            print("❌ Live transcription connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Deepgram: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        if "400" in str(e):
            print("💡 HTTP 400 suggests API key or parameter issue")
        elif "403" in str(e):
            print("💡 HTTP 403 suggests authentication/permission issue")
        elif "401" in str(e):
            print("💡 HTTP 401 suggests invalid API key")
        return False

if __name__ == "__main__":
    print("🧪 Deepgram Connection Test")
    print("=" * 30)
    
    success = test_deepgram_connection()
    
    if success:
        print("\n✅ Deepgram connection test PASSED")
        print("💡 The API key and basic connection are working")
    else:
        print("\n❌ Deepgram connection test FAILED")
        print("💡 Check your API key and network connection")
