# 🚀 Complete System Setup Guide

## 🎯 Two-Service Architecture

Your VideoSDK AI Interviewer now uses a **two-service architecture**:

### 1. **Questions API** (Port 8000) - Your Audit AI App
- **Purpose**: Provides interview questions via REST API
- **Required Endpoint**: `GET /api/questions/candidate/{candidate_id}?job_id={job_id}`
- **Response Format**:
```json
{
  "questions": [
    {
      "id": 1,
      "text": "What is your experience with Python?",
      "category": "python",
      "difficulty": "easy"
    }
  ],
  "metadata": {
    "job_id": "5",
    "candidate_id": "24",
    "job_title": "Senior Developer",
    "interview_type": "Python Technical Interview"
  }
}
```

### 2. **Transcript API** (Port 8001) - VideoSDK Service
- **Purpose**: Manages and downloads interview transcripts
- **Auto-starts**: With the VideoSDK agent
- **Endpoints**: `/transcripts/*` for transcript management

## 🔧 Setup Steps

### Step 1: Start Your Audit AI App (Port 8000)
```bash
# Your audit AI application should run on port 8000
# and provide the questions API endpoint
```

### Step 2: Start VideoSDK System
```bash
# Option A: Complete system (includes transcript API on port 8001)
python launcher.py

# Option B: Agent only (if you don't need transcript API)
set LAUNCH_MODE=agent-only
python launcher.py

# Option C: With API arguments
python main.py --job-id 5 --candidate-id 24
```

## 📊 System Flow

```
1. VideoSDK Agent starts
2. Calls YOUR audit AI app: GET http://localhost:8000/api/questions/candidate/24?job_id=5
3. Gets questions and starts interview
4. Records transcript using VideoSDK transcript system
5. Frontend can download transcript from: http://localhost:8001/transcripts/current/text
```

## ⚠️ Current Issue Resolution

**Error**: `Failed to establish connection to localhost:8001/api/questions/...`

**Root Cause**: VideoSDK is looking for questions API on port 8001, but it should look on port 8000.

**✅ Fixed**: Updated `main.py` to use port 8000 for questions API

## 🧪 Test Commands

### Test Questions API (Your Audit AI - Port 8000)
```bash
curl "http://localhost:8000/api/questions/candidate/24?job_id=5"
```

### Test Transcript API (VideoSDK - Port 8001)  
```bash
curl "http://localhost:8001/"
curl "http://localhost:8001/transcripts/"
```

### Run VideoSDK with API
```bash
python main.py --job-id 5 --candidate-id 24
```

## 📋 Checklist

- [ ] Your Audit AI app running on port 8000
- [ ] Questions API endpoint available: `/api/questions/candidate/{id}?job_id={id}`
- [ ] VideoSDK agent can connect to questions API
- [ ] Transcript API runs on port 8001 (automatic)
- [ ] Frontend download button works

## 🔄 Port Summary

| Service | Port | Purpose | Status |
|---------|------|---------|---------|
| **Your Audit AI** | 8000 | Questions API | ⚠️ Needs to be started |
| **VideoSDK Transcripts** | 8001 | Transcript downloads | ✅ Auto-starts |

The system is now properly configured with questions API on port 8000 and transcript API on port 8001!