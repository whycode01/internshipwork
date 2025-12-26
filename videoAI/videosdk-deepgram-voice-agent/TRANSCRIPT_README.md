# 📝 Transcript System Documentation

## Overview
The VideoSDK AI Interviewer now includes a comprehensive transcript system that records all conversations between the AI interviewer and candidates in textual format.

## Features

### ✅ Transcript Recording
- **Automatic Recording**: Transcripts start recording when a meeting begins
- **Real-time Capture**: Records both AI responses and user speech
- **Structured Data**: Stores speaker, message, timestamp, and confidence data
- **Text Format**: All transcripts are stored as text, not audio

### ✅ Frontend Download
- **Download Button**: Added to the chat panel interface
- **Real-time Access**: Download current conversation anytime
- **Text Format**: Downloads as formatted .txt files
- **Fallback Support**: Works with or without API server

### ✅ API Server (FastAPI)
- **RESTful API**: Complete API for transcript management
- **Multiple Endpoints**: List, download, and manage transcripts
- **JSON & Text**: Support for both JSON data and formatted text
- **CORS Enabled**: Works with frontend applications

## Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn
```

### 2. Start the System

#### Option A: Full System (Agent + API)
```bash
python launcher.py
```

#### Option B: API Server Only
```bash
set LAUNCH_MODE=api-only
python launcher.py
```

#### Option C: Agent Only (No API)
```bash
set LAUNCH_MODE=agent-only
python launcher.py
```

#### Option D: API Server Directly
```bash
python api_server.py
```

### 3. Access Endpoints
- **API Documentation**: http://localhost:8001/docs
- **List Transcripts**: http://localhost:8001/transcripts/
- **Current Transcript**: http://localhost:8001/transcripts/current
- **Download Current**: http://localhost:8001/transcripts/current/text

## File Structure

```
transcript/
├── transcript_manager.py    # Core transcript management
└── transcripts/            # Stored transcript files
    ├── interview-abc123-20241201-143022.json
    └── interview-def456-20241201-150315.json

api_server.py               # FastAPI server
launcher.py                 # Combined launcher script
```

## API Endpoints

### GET /transcripts/
List all available transcripts with metadata.

### GET /transcripts/{filename}/download
Download transcript as JSON file.

### GET /transcripts/{filename}/text
Download transcript as formatted text.

### GET /transcripts/current
Get information about currently recording transcript.

### GET /transcripts/current/text
Download current transcript as formatted text.

### POST /transcripts/start
Start a new transcript recording.

### POST /transcripts/stop
Stop current transcript recording.

## Frontend Integration

The chat panel now includes:
- **Download Button**: Green button in chat header
- **Real-time Downloads**: Download current conversation
- **API Fallback**: Works with or without API server
- **Format**: Clean, readable text format

## Example Transcript Format

```
INTERVIEW TRANSCRIPT
==================================================
Meeting ID: abc123-def456
Generated: 12/1/2024, 2:30:22 PM
Total Messages: 15

CONVERSATION:
--------------------------------------------------

[14:30:25] AI Interviewer: Hello! I'm AI Agent. Let's begin with our first question: Tell me about your experience with Python.

[14:30:45] Candidate: I have been working with Python for about 3 years, mainly in web development.

[14:30:50] AI Interviewer: That's great! Can you tell me about a specific Python project you're proud of?

==================================================
End of Transcript
```

## Integration Points

### Backend Integration
- **Agent Class**: Automatically starts/stops transcript recording
- **STT System**: Records user speech with confidence scores  
- **Intelligence**: Records AI responses
- **File Storage**: JSON files with structured data

### Frontend Integration
- **React Components**: Updated ChatPanel with download
- **TypeScript Types**: Complete type definitions
- **API Calls**: Graceful fallback to client-side generation
- **User Experience**: One-click downloads

## Configuration

### Environment Variables
- `LAUNCH_MODE`: Controls startup mode (both/api-only/agent-only)

### Storage Directory
Default: `./transcripts/`
Configurable via TranscriptManager constructor.

## Troubleshooting

### Common Issues

1. **FastAPI Not Installed**
   ```bash
   pip install fastapi uvicorn
   ```

2. **Port 8001 In Use**
   - Change port in api_server.py
   - Update frontend API calls accordingly

3. **CORS Issues**
   - Verify frontend URL in CORS middleware
   - Check browser developer console

4. **File Permissions**
   - Ensure write permissions to transcript directory
   - Check disk space availability

### Debug Mode
Start API server with debug logging:
```bash
python -m uvicorn api_server:app --host 0.0.0.0 --port 8001 --log-level debug
```