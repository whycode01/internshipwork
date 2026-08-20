# 🎯 AI Interview Management System

A comprehensive AI-powered interview management platform that uses advanced language models to generate intelligent, policy-aware interview questions tailored to company standards and candidate profiles.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation & Setup](#installation--setup)
- [Project Structure](#project-structure)
- [Key Components](#key-components)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Workflow & Data Flow](#workflow--data-flow)
- [Technologies](#technologies)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The **AI Interview Management System** is an intelligent recruitment platform designed to:

- **Generate contextual interview questions** based on job descriptions, candidate resumes, and company policies
- **Manage company policies** for compliance and cultural fit assessment
- **Track candidate interviews** with comprehensive question generation and analysis
- **Support policy-specific question generation** for targeted compliance testing
- **Maintain audit trails** for interview processes and policy-based decisions

### Key Use Cases

1. **Interview Question Generation** - Automatically generate tailored questions combining technical, behavioral, and policy-aware scenarios
2. **Policy Management** - Create and manage company policies, procedures, and compliance frameworks
3. **Candidate Screening** - Evaluate candidates on technical skills, cultural fit, and policy understanding
4. **Compliance Assessment** - Ensure candidates understand company standards and regulatory requirements

---

## 🏗️ Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Interview Management System               │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
        ┌───────▼────┐  ┌──────▼─────┐  ┌────▼────────┐
        │  Frontend   │  │  Backend   │  │  Anony API  │
        │  (React)    │  │  (FastAPI) │  │  (Node.js)  │
        └───────┬────┘  └──────┬─────┘  └────┬────────┘
                │              │              │
                └──────────────┼──────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            ┌───────▼────────┐    ┌──────▼──────────┐
            │  File Storage  │    │  LangGraph     │
            │  (JSON/CSV)    │    │  Workflow      │
            └────────────────┘    └���───────────────┘
```

### Component Interaction Flow

```
User Interface (Frontend)
      │
      ├─────> Job Management
      │       └─> Add/Edit Jobs
      │       └─> View Candidates
      │
      ├─────> Policy Management
      │       └─> Create Policies
      │       └─> Edit Policies
      │       └─> Delete Policies
      │       └─> Export Policies
      │
      ├─────> Interview Management
      │       └─> Upload Resumes
      │       └─> Generate Questions
      │       └─> Select Policies
      │       └─> Review Output
      │
      └─────────────────┐
                        │
                    REST API
                        │
            ┌───────────┴───────────┐
            │                       │
        FastAPI Backend         LangGraph
        (Job & Policy API)      (Workflow)
            │                       │
            ├─> Question Generation │
            ├─> Policy Loading      │
            ├─> Data Processing     │
            └─> File Operations     │
                                    │
                            AI Model Integration
                            (OpenAI, etc.)
```

---

## ✨ Features

### 1. **Policy-Enhanced Question Generation** ✓
- Generate interview questions using three key inputs:
  - 📋 Job Description
  - 👤 Resume/CV
  - 🏢 Company Policies (NEW!)
- Questions now test:
  - Technical skills
  - Behavioral competencies
  - Policy understanding & compliance
  - Cultural fit with company values
  - Real-world scenario handling

### 2. **Policy-Specific Question Generation** ✓
- Select specific policies for tailored question generation
- Focus on particular compliance areas
- Role-aligned policy testing

### 3. **Policy Management System** ✓
- Create, read, update, delete policies
- Manage report templates
- Export policies as JSON
- Real-time loading and error handling
- User-friendly interface

### 4. **Comprehensive Interview Management** ✓
- Job posting management
- Candidate profile management
- Resume upload and parsing
- Question generation with audit trails
- Interview tracking

### 5. **Advanced AI Integration** ✓
- LangGraph workflow orchestration
- Multi-step question generation
- Context-aware prompt engineering
- Follow-up question generation

---

## 📋 System Requirements

### Prerequisites
- **Docker** & **Docker Compose** (Latest versions)
- **Node.js** 16+ (for frontend development)
- **Python** 3.9+ (for backend development)
- **Git** for version control

### Hardware Requirements
- Minimum: 2GB RAM, 2 CPU cores
- Recommended: 4GB+ RAM, 4+ CPU cores
- 2GB free disk space

### Environment Setup
- OpenAI API key (for AI features)
- Modern web browser (Chrome, Firefox, Safari, Edge)

---

## 🚀 Installation & Setup

### Quick Start with Docker Compose

#### 1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd ai-project-repo
```

#### 2. **Configure Environment Variables**

Create a `.env` file in the backend directory:
```bash
cd backend
cat > .env << EOF
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./test.db
ENVIRONMENT=development
EOF
```

#### 3. **Build and Start Services**
```bash
# From the project root
docker compose up --build
```

#### 4. **Access the Application**
- **Frontend**: [http://localhost:4173](http://localhost:4173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 5. **Verify Installation**
```bash
# Check if all services are running
docker compose ps

# View logs
docker compose logs -f
```

#### 6. **Stop Services**
```bash
docker compose down
```

### Manual Installation (Development)

#### Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
ai-project-repo/
├── backend/
│   ├── routers/
│   │   ├── jobs.py              # Job and question generation endpoints
│   │   ├── policies.py          # Policy management endpoints
│   │   └── ...
│   ├── prompts/
│   │   ├── job_prompts.py       # Prompt templates for question generation
│   │   └── ...
│   ├── workflows/
│   │   ├── interview_workflow.py # LangGraph workflow definitions
│   │   └── ...
│   ├── storage/
│   │   ├── policies/            # Stored policy files (JSON)
│   │   ├── templates/           # Report templates
│   │   └── ...
│   ├── main.py                  # FastAPI application entry point
│   ├── sql_ops.py              # Database operations
│   ├── config.json             # Configuration file
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Docker configuration
│   └── langgraph.json          # LangGraph configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Jobs.jsx         # Job management component
│   │   │   ├── Candidates.jsx   # Candidate management
│   │   │   ├── Policies.jsx     # Policy management
│   │   │   ├── Manage.jsx       # Interview management
│   │   │   └── ...
│   │   ├── pages/
│   │   ├── App.jsx              # Main app component
│   │   └── main.jsx             # Entry point
│   ├── public/
│   ├── package.json             # Node dependencies
│   ├── Dockerfile               # Docker configuration
│   ├── vite.config.js          # Vite configuration
│   └── index.html
│
├── anony-api/
│   └── ...                      # Anonymization API services
│
├── docker-compose.yml           # Multi-container orchestration
├── README.md                    # This file
├── POLICIES_INTEGRATION.md      # Policies integration guide
├── POLICY_SELECTION_FEATURE.md  # Policy selection feature guide
└── SEPARATION_IMPLEMENTATION.md # Implementation details
```

---

## 🔧 Key Components

### 1. **Backend (FastAPI)**

#### Main Entry Point: `main.py`
```python
# Initializes FastAPI application
# Registers routers for jobs, policies, candidates
# Configures CORS for frontend communication
```

#### Routers

##### `routers/jobs.py` - Job & Question Management
- `POST /api/jobs/` - Create new job
- `GET /api/jobs/{job_id}` - Get job details
- `POST /api/jobs/questions/{job_id}/{candidate_id}` - Generate questions
- `POST /api/jobs/candidates/{job_id}` - Add candidate to job

##### `routers/policies.py` - Policy Management
- `POST /api/policies` - Create policy
- `GET /api/policies/{policy_type}` - Get all policies
- `GET /api/policies/{policy_type}/{policy_id}` - Get specific policy
- `PUT /api/policies/{policy_type}/{policy_id}` - Update policy
- `DELETE /api/policies/{policy_type}/{policy_id}` - Delete policy
- `GET /api/policies/{policy_type}/{policy_id}/export` - Export policy

#### Data Processing: `sql_ops.py`
- Database operations
- Candidate profile management
- Job data persistence
- Question storage and retrieval

#### Prompt Engineering: `prompts/job_prompts.py`
- First-round question generation prompts
- Policy-enhanced prompt templates
- Follow-up question prompts
- Scenario-based question templates

### 2. **Frontend (React + Vite)**

#### Key Components

##### `Policies.jsx` - Policy Management
- Create/edit/delete policies
- Switch between policies and templates
- Export functionality
- Real-time error handling

##### `Jobs.jsx` - Job Management
- Create job postings
- View all jobs
- Manage candidates per job
- Navigation to other modules

##### `Candidates.jsx` - Candidate Management
- Upload resumes
- Store candidate profiles
- Link candidates to jobs

##### `Manage.jsx` - Interview Management
- Policy selection dropdown
- Generate interview questions
- Review generated questions
- Track interview status
- Support for audit mode

### 3. **LangGraph Workflows**

#### Interview Workflow: `workflows/interview_workflow.py`
- Multi-step question generation pipeline
- Policy loading and processing
- Prompt formatting and delivery
- Response parsing and formatting
- Follow-up question generation

---

## 📊 Workflow & Data Flow

### Question Generation Flow

```
┌─────────────────┐
│  User Initiates │
│ Question Gen    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Collect Input Data:                 │
│ - Job Description                   │
│ - Candidate Resume                  │
│ - Selected Policy (if any)          │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Load Policies from Storage          │
│ - storage/policies/                 │
│ - Apply filters if policy selected  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Build Prompt Context:               │
│ - Job requirements                  │
│ - Resume highlights                 │
│ - Policy content                    │
│ - Question type specifications      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Call LangGraph Workflow             │
│ - Execute workflow nodes            │
│ - Interact with AI Model            │
│ - Generate questions                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Parse & Format Response             │
│ - Structure questions               │
│ - Add metadata                      │
│ - Prepare for display               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Store Results                       │
│ - Save to database/files            │
│ - Create audit trail                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Display to Frontend                 │
│ - Return via API                    │
│ - Render in UI                      │
└─────────────────────────────────────┘
```

### Policy Integration in Question Generation

```
Input: Job + Resume + Policy Selection
                │
                ▼
        Load Policy Content
                │
                ▼
    ┌───────────┴───────────────────┐
    │                               │
    ▼                               ▼
Specific Policy                All Policies
    │                               │
    └───────────┬───────────────────┘
                │
                ▼
        Build Enhanced Prompt
    Includes 3 question types:
    1. Technical Questions
    2. Behavioral Questions
    3. Policy/Compliance Questions
                │
                ▼
    Generate Policy-Aware Questions
```

---

## 💻 Technologies

### Backend
- **Framework**: FastAPI (Python web framework)
- **Workflow**: LangGraph (Agent workflow orchestration)
- **AI Integration**: OpenAI API / LangChain
- **Database**: SQLite (default)
- **Validation**: Pydantic
- **API Docs**: Swagger/OpenAPI

### Frontend
- **Framework**: React 18+
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router
- **Icons**: Lucide React

### Deployment
- **Containerization**: Docker & Docker Compose
- **Container Orchestration**: Docker Compose
- **Network**: NGINX (reverse proxy in compose)

### Development Tools
- **Version Control**: Git
- **Environment Management**: Python venv, npm/yarn
- **Code Quality**: ESLint, Black (optional)

---

## ⚙️ Configuration

### Backend Configuration: `backend/config.json`

```json
{
  "app_name": "AI Interview Management System",
  "api_version": "v1",
  "environment": "development",
  "database": {
    "url": "sqlite:///./test.db"
  },
  "ai_model": {
    "provider": "openai",
    "model": "gpt-4"
  },
  "storage": {
    "policies_dir": "storage/policies/",
    "templates_dir": "storage/templates/"
  }
}
```

### Environment Variables

Create `.env` in backend directory:
```bash
# AI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Database
DATABASE_URL=sqlite:///./test.db

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Frontend URL
FRONTEND_URL=http://localhost:5173

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Docker Compose Configuration: `docker-compose.yml`

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=sqlite:///./test.db

  frontend:
    build: ./frontend
    ports:
      - "4173:4173"
    depends_on:
      - backend
```

---

## 🧪 Testing

### Backend API Testing

#### Using the Test Script
```bash
cd backend
python test_policies_api.py
```

#### Manual Testing with curl
```bash
# Create a policy
curl -X POST http://localhost:8000/api/policies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Privacy Policy",
    "content": "Policy content here...",
    "type": "policies"
  }'

# Get all policies
curl http://localhost:8000/api/policies/policies

# Generate questions
curl -X POST http://localhost:8000/api/jobs/questions/1/1 \
  -H "Content-Type: application/json" \
  -d '{"policyId": "policy_id_here"}'
```

#### Using Postman
- Import the API collection
- Configure base URL: `http://localhost:8000`
- Test each endpoint with sample data

### Frontend Testing

```bash
cd frontend
npm install
npm run dev

# In browser: http://localhost:5173
```

#### Manual Test Scenarios
1. Create policies via Policies Management
2. Create job posting
3. Upload candidate resume
4. Generate questions with specific policy selected
5. Verify questions reflect policy content
6. Export policies and verify format

### Integration Testing

```bash
cd backend
python test_policy_integration.py
```

This runs:
- Sample policy creation
- Enhanced question generation
- Policy-specific question generation
- Comparison of basic vs. enhanced prompts

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **"Connection refused" on port 8000**
```bash
# Check if backend is running
docker compose ps

# Rebuild and restart
docker compose down
docker compose up --build
```

#### 2. **Frontend can't reach backend**
- Verify backend is running: `http://localhost:8000/docs`
- Check API_BASE_URL in frontend `.env` or component
- Ensure CORS is enabled in backend

#### 3. **Policy file not found**
```bash
# Check storage directory exists
ls -la backend/storage/policies/

# Create if missing
mkdir -p backend/storage/policies/
mkdir -p backend/storage/templates/
```

#### 4. **OpenAI API key issues**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API connection
python -c "import openai; print(openai.__version__)"
```

#### 5. **Database errors**
```bash
# Reset database
rm backend/test.db

# Reinitialize
python -c "from sql_ops import init_db; init_db()"
```

### Logs & Debugging

```bash
# View all service logs
docker compose logs -f

# View specific service
docker compose logs -f backend
docker compose logs -f frontend

# Debug mode (if supported)
docker compose up --build --verbose
```

---

## 📚 Usage Guide

### For Recruiters

#### 1. Create a Job Posting
1. Navigate to Jobs section
2. Click "Create New Job"
3. Enter job details (title, description, requirements)
4. Save

#### 2. Set Up Company Policies
1. Go to Policies Management
2. Click "Create Policy"
3. Enter policy name and content
4. Repeat for each policy (compliance, code of conduct, etc.)

#### 3. Upload Candidate Resume
1. Select job posting
2. Click "Add Candidate"
3. Upload resume (PDF/DOCX/TXT)
4. Save candidate profile

#### 4. Generate Interview Questions
1. Open Manage section for candidate
2. (Optional) Select specific policy for tailored questions
3. Click "Generate Questions"
4. Review generated questions
5. Export or print for interview

#### 5. Review & Audit
1. View all generated questions
2. Track which policies were considered
3. Export interview summary

### For System Administrators

#### Policy Management
- Regularly update company policies
- Archive outdated policies
- Maintain policy version history
- Test policy integration regularly

#### System Monitoring
- Check service health
- Monitor API performance
- Review error logs
- Backup policies and data

#### User Support
- Help users navigate workflow
- Train on policy selection
- Troubleshoot API issues
- Manage system upgrades

---

## 🚀 Advanced Features

### Policy-Enhanced Question Generation

Questions are now generated in three types:

#### 1. **Policy/Compliance Questions**
Test understanding of company policies and compliance requirements.

**Example:**
> "Based on our data privacy policy, how would you handle a situation where a stakeholder requests access to customer data that could help with analysis but falls outside their authorization?"

#### 2. **Cultural Fit Questions**
Assess alignment with company values and ethical standards.

**Example:**
> "Describe a time when you had to choose between meeting a deadline and following proper documentation procedures. How did you handle it?"

#### 3. **Enhanced Scenario Questions**
Real situations based on actual policies combining technical and compliance aspects.

**Example:**
> "You discover a dataset contains more personal information than expected. Walk through your immediate actions based on our privacy policy."

---

## 📈 Performance & Scaling

### Current Capacity
- Supports 100+ policies
- Generates 5-10 questions per request
- Processes resumes up to 10 pages

### Optimization Tips
- Cache loaded policies
- Use specific policy selection to reduce context size
- Batch generate for multiple candidates
- Monitor API rate limits

---

## 🔐 Security Considerations

- Store API keys securely in environment variables
- Validate all user inputs
- Sanitize file uploads
- Use HTTPS in production
- Implement authentication for production
- Restrict policy access to authorized users

---

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

---

## 📞 Support & Documentation

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- **Policy Integration Guide**: See `POLICIES_INTEGRATION.md`
- **Policy Selection Feature**: See `POLICY_SELECTION_FEATURE.md`
- **Implementation Details**: See `SEPARATION_IMPLEMENTATION.md`

---

## 📄 License

This project is part of the internship work program. Refer to the main repository license.

---

## 🙏 Acknowledgments

- Built with FastAPI, React, and LangGraph
- Powered by OpenAI's language models
- Docker for containerization
- Community contributions and feedback

---

**Last Updated:** August 2026  
**Version:** 1.0.0  
**Status:** Active Development

For questions or issues, please open an issue on GitHub or contact the development team.
