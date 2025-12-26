#!/bin/bash
# Development setup script for VideoSDK AI Interview Agent

echo "🚀 Starting VideoSDK AI Interview Agent Development Environment"
echo "================================================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

echo "📋 Starting services..."

# Start API server in background
echo "🌐 Starting Transcript API Server (Port 8001)..."
start cmd /k "cd /d \"$(pwd)\" && \"$(pwd)/venv/Scripts/python.exe\" api_server.py"

# Wait a moment for API server to start
sleep 3

# Start React development server
echo "⚛️  Starting React Client (Port 5173)..."
cd client
start cmd /k "npm run dev"

echo ""
echo "✅ Development environment started!"
echo ""
echo "🔗 Available Services:"
echo "   • React Client: http://localhost:5173"
echo "   • Transcript API: http://localhost:8001"
echo "   • API Documentation: http://localhost:8001/docs"
echo ""
echo "🎯 Features Available:"
echo "   • Push-to-Talk Button with voice activity detection"
echo "   • Organized transcript storage (job-id/candidate-id)"
echo "   • Multiple API endpoints for audit AI integration"
echo "   • Optimized bundle with code splitting"
echo ""
echo "📝 To test push-to-talk:"
echo "   1. Open http://localhost:5173"
echo "   2. Start a meeting"
echo "   3. Use the push-to-talk button to speak"
echo "   4. Check transcripts at http://localhost:8001/docs"