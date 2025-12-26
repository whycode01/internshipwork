# Port Configuration Summary

## 🎯 Port Allocation

### Port 8000 - Questions API (Your Audit AI App)
- **Purpose**: Main application with questions API endpoints
- **Endpoints**: `/api/questions/candidate/{id}?job_id={job_id}`
- **Used by**: VideoSDK agent for fetching interview questions
- **Status**: Available for your audit AI app

### Port 8001 - Transcript API (VideoSDK)
- **Purpose**: Transcript download and management
- **Endpoints**: `/transcripts/*` endpoints
- **Used by**: Frontend download button and transcript management
- **Status**: VideoSDK transcript-specific server

## ✅ Updated Configuration

### Questions API (Port 8000)
- `main.py` default API URL: `http://localhost:8000`
- Used for fetching interview questions
- Should be provided by your audit AI application

### Transcript API (Port 8001)  
- `api_server.py` runs on port 8001
- `ChatPanel.tsx` calls port 8001 for downloads
- Independent transcript management service

## 🚀 New Access Points

- **API Server**: http://localhost:8001/
- **API Documentation**: http://localhost:8001/docs
- **Transcript Endpoints**: http://localhost:8001/transcripts/
- **Current Transcript**: http://localhost:8001/transcripts/current/text

## 🔧 How to Start

### Option 1: Complete System
```bash
python launcher.py
```

### Option 2: API Server Only  
```bash
python api_server.py
```

### Option 3: Manual Uvicorn
```bash
python -m uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
```

## ✅ Verified Working

- ✅ API server starts on port 8001
- ✅ All endpoints accessible 
- ✅ Frontend download button uses new port
- ✅ No conflicts with port 8000 (free for audit AI app)

## 📝 Note

Your audit AI app can now safely use port 8000 without any conflicts. The VideoSDK transcript system will run on port 8001.