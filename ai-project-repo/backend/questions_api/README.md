# Interview Questions API

A FastAPI-based REST API service that serves AI-generated interview questions from CSV files to external applications.

## 🚀 Features

- **CSV-to-JSON Conversion**: Automatically converts CSV question files to structured JSON responses
- **Multiple Query Options**: Search by candidate ID, job ID, policy/category, or advanced filters
- **Automatic File Discovery**: Scans and indexes CSV files automatically
- **Pagination Support**: Built-in pagination for large question sets
- **Real-time Documentation**: Auto-generated OpenAPI docs at `/docs`
- **High Performance**: Async/await patterns with caching for optimal performance

## 📁 File Structure Expected

The API expects CSV files in this directory structure:
```
storage/jobs/{job_id}_{job_category}/interview_questions_{candidate_id}_{timestamp}.csv
```

Example:
```
storage/jobs/5_corporate_roles/interview_questions_24_20250908_095937.csv
```

## 🔧 Installation

1. **Install Dependencies**:
```bash
cd backend/questions_api
pip install -r requirements.txt
```

2. **Run the API**:
```bash
python run.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health information

### Questions
- `GET /api/questions/candidate/{candidate_id}` - All questions for a candidate
- `GET /api/questions/candidate/{candidate_id}/job/{job_id}` - Questions for specific candidate and job
- `GET /api/questions/job/{job_id}/latest` - Latest questions for a job
- `GET /api/questions/policy/{policy_name}` - Questions by policy/job category
- `GET /api/questions/search` - Advanced search with filters

### Admin
- `GET /api/questions/files/index` - File index information
- `POST /api/questions/files/refresh` - Refresh file index

## 🔍 Query Parameters

- `limit` (1-100): Number of results per page
- `offset` (≥0): Number of results to skip
- `question_type`: Filter by question type (Behavioral, Technical, etc.)
- `sort_by`: Sort by field (timestamp, question_type)
- `query`: Search text in question content

## 📊 Response Format

All endpoints return JSON in this format:
```json
{
  "status": "success",
  "data": {
    "metadata": {
      "candidate_id": 24,
      "job_id": 5,
      "job_category": "corporate_roles",
      "policy_context": "Corporate Finance Analyst",
      "generated_at": "2025-09-08T09:59:37Z",
      "source_file": "jobs/5_corporate_roles/interview_questions_24_20250908_095937.csv",
      "total_questions": 12
    },
    "questions": [
      {
        "id": 1,
        "question_text": "Can you describe a situation where you had to analyze a large dataset?",
        "question_type": "Behavioral",
        "objective": "Assess ability to analyze complex data and communicate insights",
        "metadata": {
          "difficulty": "intermediate",
          "estimated_time": "5-7 minutes",
          "skills_assessed": ["data_analysis", "communication"]
        }
      }
    ]
  },
  "pagination": {
    "current_page": 1,
    "total_pages": 2,
    "total_items": 12,
    "items_per_page": 10,
    "has_next": true,
    "has_previous": false
  }
}
```

## 🎯 Example Usage

### Get All Questions for Candidate 24
```bash
curl "http://localhost:8000/api/questions/candidate/24?limit=5"
```

### Get Questions for Specific Job and Candidate
```bash
curl "http://localhost:8000/api/questions/candidate/24/job/5"
```

### Search Questions by Type
```bash
curl "http://localhost:8000/api/questions/search?question_type=Behavioral&limit=10"
```

### Get Questions by Policy
```bash
curl "http://localhost:8000/api/questions/policy/corporate_roles"
```

### Advanced Search
```bash
curl "http://localhost:8000/api/questions/search?query=data%20analysis&candidate_id=24&question_type=Technical"
```

## 🔧 Configuration

Environment variables (prefix with `QUESTIONS_API_`):
- `STORAGE_PATH`: Path to CSV files (default: "../storage/jobs")
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: False)
- `LOG_LEVEL`: Logging level (default: "INFO")

## 📱 Integration Example

### Python Client
```python
import requests

# Get questions for candidate 24
response = requests.get("http://localhost:8000/api/questions/candidate/24")
data = response.json()

questions = data["data"]["questions"]
for question in questions:
    print(f"Q: {question['question_text']}")
    print(f"Type: {question['question_type']}")
    print(f"Objective: {question['objective']}")
    print("---")
```

### JavaScript Client
```javascript
// Fetch questions for a candidate
async function getQuestions(candidateId) {
    const response = await fetch(`http://localhost:8000/api/questions/candidate/${candidateId}`);
    const data = await response.json();
    return data.data.questions;
}

// Use the questions
getQuestions(24).then(questions => {
    questions.forEach(q => {
        console.log(`${q.question_type}: ${q.question_text}`);
    });
});
```

## 🚀 Production Deployment

For production deployment:

1. Set `DEBUG=False`
2. Configure proper CORS origins
3. Use a production ASGI server like Gunicorn
4. Set up proper logging and monitoring
5. Consider adding authentication/authorization

```bash
# Production example
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📝 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔍 Monitoring

The API provides these monitoring endpoints:
- `/health` - Health status
- `/api/questions/files/index` - File index statistics
- Built-in logging for all requests and errors

## 🎯 Integration Tips

1. **Caching**: The API caches parsed CSV content for better performance
2. **Pagination**: Always use pagination for large datasets
3. **Error Handling**: Check the `status` field in responses
4. **File Monitoring**: Use the admin endpoints to monitor file indexing
5. **Search**: Use the search endpoint for complex queries across multiple criteria
