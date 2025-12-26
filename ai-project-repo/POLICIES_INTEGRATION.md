# Policies Management Integration

This document explains the integration between the frontend Policies component and the backend API, **including how policies now enhance interview question generation**.

## 🎯 Enhanced Question Generation

### **YES - Questions are now generated based on Resume + Policies!**

The system has been enhanced to generate interview questions using three key inputs:

1. **📋 Job Description** - Requirements, skills, role expectations
2. **👤 Resume/CV** - Candidate background, experience, skills  
3. **🏢 Company Policies** - Compliance requirements, values, standards *(NEW!)*

### How It Works

When generating interview questions, the system now:

1. **Loads all company policies** from the policies management system
2. **Analyzes policy content** for compliance requirements and company values
3. **Generates enhanced questions** that test:
   - Technical skills (as before)
   - Experience and behavioral aspects (as before)
   - **Policy understanding and compliance** *(NEW!)*
   - **Cultural fit with company values** *(NEW!)*
   - **Real-world scenario handling** within policy framework *(NEW!)*

### Enhanced Question Types

The system now generates these additional question types:

#### 🔒 Policy/Compliance Questions
- Test understanding of company policies
- Evaluate compliance awareness
- Check ethical decision-making

**Example:**
> "Based on our data privacy policy, describe how you would handle a situation where a stakeholder requests access to customer data that could help with their analysis but falls outside their authorized scope."

#### 🎭 Cultural Fit Questions  
- Assess alignment with company values
- Test cultural awareness
- Evaluate ethical standards

**Example:**
> "Describe a time when you had to choose between meeting a tight deadline and following proper documentation procedures. How did you handle it, and what was the outcome?"

#### 🎯 Enhanced Scenario Questions
- Realistic situations based on actual policies
- Test practical application of policy knowledge
- Combine technical skills with compliance requirements

**Example:**
> "You discover that a dataset you're analyzing contains more personal information than expected. Walk me through your immediate actions based on our privacy policy."

## 🔧 Technical Implementation

### Backend Changes

#### 1. Enhanced Question Generation (`backend/routers/jobs.py`)
- **`load_policies()`**: New function that loads all policies from storage
- **`first_questions_prompt()`**: Enhanced to include policies parameter
- **`generate_first_questions()`**: Now loads and includes policies
- **`second_questions_prompt()`**: Enhanced for policy-aware follow-up questions

#### 2. Enhanced Prompts (`backend/prompts/job_prompts.py`)
- **`prompt1_with_policies`**: New prompt template including policy context
- **`prompt2_with_policies`**: Enhanced follow-up prompt with policy considerations

### Key Changes Made

```python
# Before: Basic question generation
prompt = first_questions_prompt(job, candidate['aspects'], candidate['resume'])

# After: Policy-enhanced question generation  
policies = load_policies()
prompt = first_questions_prompt(job, candidate['aspects'], candidate['resume'], policies)
```

### Policy Loading Process

1. **Scan policies directory**: `storage/policies/`
2. **Load all policy JSON files**: Extract name and content
3. **Include relevant templates**: Policy-related report templates
4. **Combine into single string**: Format for AI prompt
5. **Pass to question generation**: Include in prompt context

### Prompt Structure

The enhanced prompt now includes:

```
**Input Data**
1. Job Information: [job details]
2. Candidate Resume: [resume content]  
3. Company Policies & Guidelines: [policy content] ← NEW!
```

## Backend API Endpoints

The backend provides a RESTful API for managing policies and report templates at `/api/policies`.

### Base URL
```
http://localhost:8000/api/policies
```

### Endpoints

#### 1. Create Policy/Template
- **Method**: `POST`
- **URL**: `/api/policies`
- **Body**:
```json
{
  "name": "Policy Name",
  "content": "Policy content here...",
  "type": "policies" // or "report_templates"
}
```
- **Response**:
```json
{
  "success": true,
  "message": "Policy created successfully",
  "data": {
    "id": "policy_name_20250726_123456",
    "name": "Policy Name",
    "content": "Policy content here...",
    "type": "policies",
    "created_at": "2025-07-26T12:34:56.789Z",
    "updated_at": "2025-07-26T12:34:56.789Z"
  }
}
```

#### 2. Get All Policies/Templates
- **Method**: `GET`
- **URL**: `/api/policies/{policy_type}` (where policy_type is "policies" or "report_templates")
- **Response**:
```json
{
  "success": true,
  "message": "Retrieved 5 policies",
  "data": [
    {
      "id": "policy_name_20250726_123456",
      "name": "Policy Name",
      "content": "Policy content here...",
      "type": "policies",
      "created_at": "2025-07-26T12:34:56.789Z",
      "updated_at": "2025-07-26T12:34:56.789Z"
    }
  ]
}
```

#### 3. Get Single Policy/Template
- **Method**: `GET`
- **URL**: `/api/policies/{policy_type}/{policy_id}`
- **Response**: Same as create response

#### 4. Update Policy/Template
- **Method**: `PUT`
- **URL**: `/api/policies/{policy_type}/{policy_id}`
- **Body**:
```json
{
  "name": "Updated Policy Name", // optional
  "content": "Updated content..." // optional
}
```
- **Response**: Same as create response

#### 5. Delete Policy/Template
- **Method**: `DELETE`
- **URL**: `/api/policies/{policy_type}/{policy_id}`
- **Response**:
```json
{
  "success": true,
  "message": "Policy deleted successfully"
}
```

#### 6. Export Policy/Template
- **Method**: `GET`
- **URL**: `/api/policies/{policy_type}/{policy_id}/export`
- **Response**: JSON file download

## Frontend Integration

### Component Location
```
frontend/src/components/Policies.jsx
```

### Route
```
/jobs/policies
```

### Features
1. **Type Selection**: Switch between policies and report templates
2. **Create New**: Create new policies/templates with name and content
3. **Edit Existing**: Select and edit existing policies/templates
4. **Delete**: Remove policies/templates with confirmation
5. **Export**: Download policies/templates as JSON files
6. **Real-time Loading**: Shows loading states and error handling
7. **Success/Error Messages**: User feedback for all operations

### State Management
The component manages the following state:
- `selectedType`: Current document type (policies/report_templates)
- `selectedOption`: Currently selected policy ID for editing
- `policyName`: Policy/template name input
- `policyText`: Policy/template content input
- `existingPolicies`: List of all policies/templates
- `isLoading`: Loading state for API calls
- `error`: Error messages
- `success`: Success messages
- `isEditing`: Whether currently editing an existing policy
- `editingPolicyId`: ID of the policy being edited

### Navigation
A "Policies Management" link has been added to the sidebar, visible only when in the "Interview Audit" mode (jobs section).

## File Storage

### Backend Storage
- Policies are stored in: `backend/storage/policies/`
- Templates are stored in: `backend/storage/templates/`
- Each policy/template is stored as a separate JSON file named with the generated ID

### File Structure
```
storage/
├── policies/
│   └── policy_name_20250726_123456.json
└── templates/
    └── template_name_20250726_123456.json
```

## Testing

### Backend API Testing
Use the test script at `backend/test_policies_api.py` to test all API endpoints:

```bash
cd backend
python test_policies_api.py
```

### Policy Integration Testing
Use the enhanced test script to verify policy integration:

```bash
cd backend  
python test_policy_integration.py
```

This script will:
1. Create sample policies
2. Demonstrate enhanced question generation
3. Show the difference between basic and policy-enhanced prompts
4. Explain new question types available

### Frontend Testing
1. Start the backend server:
```bash
cd backend
python main.py
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Navigate to `http://localhost:5173/jobs/policies`
4. Create some policies (e.g., Data Privacy Policy, Code of Conduct)
5. Generate interview questions for a candidate
6. Review the generated questions to see policy integration

### Complete Workflow Testing

1. **Create Policies**: Use Policies Management to add company policies
2. **Upload Resume**: Add a candidate with resume
3. **Generate Questions**: Run question generation process  
4. **Review Output**: Check that questions include policy-related content
5. **Verify Enhancement**: Compare with previous question sets

## 📊 Benefits of Policy Integration

### For Recruiters
- **Comprehensive Assessment**: Test both technical skills and cultural fit
- **Compliance Screening**: Identify candidates who understand regulations
- **Realistic Scenarios**: Questions based on actual company situations
- **Standardized Process**: Consistent policy-based evaluation

### For Organizations  
- **Risk Mitigation**: Screen for compliance awareness early
- **Cultural Alignment**: Ensure candidates fit company values
- **Quality Hiring**: Better candidate-company match
- **Audit Trail**: Document policy-aware hiring decisions

### For Candidates
- **Clear Expectations**: Understand company standards upfront
- **Relevant Questions**: Scenarios they'll actually face on the job
- **Fair Assessment**: Evaluated on complete skill set including compliance
- **Professional Growth**: Learn about industry best practices

## 🚀 Future Enhancements

1. **Advanced Policy Mapping**: Match specific policies to job roles
2. **Dynamic Question Weighting**: Adjust policy question ratio based on role
3. **Policy Updates**: Auto-refresh questions when policies change
4. **Compliance Scoring**: Rate candidates on policy understanding
5. **Industry Templates**: Pre-built policy sets for different sectors

## Error Handling

### Backend
- Input validation using Pydantic models
- File system error handling
- HTTP status codes for different error types
- Detailed error messages in API responses

### Frontend
- Network error handling
- User-friendly error messages
- Loading states during API calls
- Form validation before submission

## Dependencies

### Backend
- FastAPI: Web framework
- Pydantic: Data validation
- Python standard library: File operations

### Frontend
- React: UI framework
- Axios: HTTP client
- React Router: Navigation
- Lucide React: Icons
- Tailwind CSS: Styling

## Next Steps

1. **Authentication**: Add user authentication to secure policy management
2. **Permissions**: Implement role-based access control
3. **Versioning**: Add policy versioning and history tracking
4. **Import**: Add functionality to import policies from files
5. **Templates**: Create predefined policy templates
6. **Search**: Add search and filtering capabilities
7. **Validation**: Add policy content validation rules
