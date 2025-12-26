#!/usr/bin/env python3
"""
Launcher script for VideoSDK AI Interviewer with Transcript API
Starts both the AI agent and the FastAPI transcript server
"""

import asyncio
import os
import subprocess
import sys
import time
from threading import Thread


def start_api_server():
    """Start the FastAPI transcript server"""
    print("🚀 Starting FastAPI Transcript Server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_server:app", 
            "--host", "0.0.0.0", 
            "--port", "8001", 
            "--reload"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start API server: {e}")
    except KeyboardInterrupt:
        print("🛑 API server stopped")

def start_ai_agent():
    """Start the AI agent"""
    print("🤖 Starting AI Agent...")
    try:
        # Import and run the main agent
        from main import main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 AI Agent stopped")
    except Exception as e:
        print(f"❌ AI Agent error: {e}")

def main():
    """Main launcher function"""
    print("🎬 VideoSDK AI Interviewer with Transcript API")
    print("=" * 50)
    
    # Check if dependencies are installed
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI dependencies found")
    except ImportError:
        print("❌ FastAPI dependencies not installed")
        print("   Run: pip install fastapi uvicorn")
        return
    
    try:
        # Start API server in a separate thread
        api_thread = Thread(target=start_api_server, daemon=True)
        api_thread.start()
        
        # Wait a moment for API server to start
        time.sleep(3)
        print("⏳ API server should be starting...")
        
        # Check if user wants to run agent or just API
        mode = os.getenv("LAUNCH_MODE", "both")  # both, api-only, agent-only
        
        if mode == "api-only":
            print("🔧 Running in API-only mode")
            print("📊 Access API docs at: http://localhost:8001/docs")
            print("🌐 API endpoints at: http://localhost:8001/")
            api_thread.join()  # Wait for API thread
        elif mode == "agent-only":
            print("🔧 Running in Agent-only mode")
            start_ai_agent()
        else:
            print("🔧 Running in both API + Agent mode")
            print("📊 API available at: http://localhost:8001/")
            
            # Start AI agent in main thread
            start_ai_agent()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Launcher error: {e}")

if __name__ == "__main__":
    main()