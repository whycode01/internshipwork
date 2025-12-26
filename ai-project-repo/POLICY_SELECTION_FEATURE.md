# Policy-Specific Question Generation Feature

## 🎯 Overview

This feature adds a **policy selection dropdown** to the Manage section, allowing you to generate interview questions tailored to specific company policies instead of using all policies at once.

## ✨ New Feature: Policy Selection in Manage Section

### 📍 Location
- **Path**: `/jobs/candidates/screening?jobId=X&candidateId=Y` (Manage section)
- **Visibility**: Only appears for **job interviews** (not audit processes)
- **Position**: Above the "Generate Questions" button

### 🎛️ UI Components

#### Policy Selection Dropdown
```jsx
// Dropdown with policy options
<select>
  <option value="">All Available Policies</option>
  <option value="policy_id_1">Data Privacy Policy</option>
  <option value="policy_id_2">Code Quality Standards</option>
  <option value="policy_id_3">Remote Work Policy</option>
</select>
```

#### Helper Text
- **When policy selected**: "Questions will be tailored to the selected policy"
- **When no policy selected**: "Questions will consider all available policies"

#### Loading States
- Shows spinner while loading policies
- Disables dropdown during policy fetch

## 🔄 How It Works

### 1. **Policy Loading**
```javascript
// Frontend automatically loads available policies
const response = await axios.get('/api/policies/policies');
setAvailablePolicies(response.data.data);
```

### 2. **Policy Selection**
```javascript
// User selects a specific policy
const [selectedPolicyId, setSelectedPolicyId] = useState('');
```

### 3. **Enhanced Question Generation**
```javascript
// Include selected policy in generation request
const requestData = {
  policyId: selectedPolicyId // or null for all policies
};
await axios.post(`/api/jobs/questions/${jobId}/${candidateId}`, requestData);
```

### 4. **Backend Processing**
```python
# Backend loads specific policy or all policies
policies = load_policies(specific_policy_id)
prompt = first_questions_prompt(job, aspects, resume, policies)
```

## 🎯 Question Generation Scenarios

### Scenario 1: No Policy Selected (Default)
- **Behavior**: Uses all available policies
- **Questions**: Broad coverage of all company standards
- **Use Case**: General assessment

### Scenario 2: Specific Policy Selected
- **Behavior**: Focuses on selected policy only
- **Questions**: Tailored to specific policy requirements
- **Use Case**: Role-specific compliance testing

## 📋 Example Policy-Tailored Questions

### Data Privacy Policy Selected
```
"Based on our data privacy policy, how would you handle a situation where 
a manager requests access to customer data for a project that doesn't 
directly involve those customers?"
```

### Code Quality Standards Selected
```
"Our development standards require 80% test coverage. Walk me through 
how you would implement testing for a new feature while meeting this 
requirement and ensuring code quality."
```

### Remote Work Policy Selected
```
"Describe how you would handle a situation where you need to collaborate 
with team members across different time zones while maintaining our 
core hours requirement of 10 AM - 3 PM overlap."
```

## 🔧 Technical Implementation

### Frontend Changes (`Manage.jsx`)

#### New State Variables
```javascript
const [availablePolicies, setAvailablePolicies] = useState([]);
const [selectedPolicyId, setSelectedPolicyId] = useState('');
const [loadingPolicies, setLoadingPolicies] = useState(false);
const [showPolicySelection, setShowPolicySelection] = useState(false);
```

#### Policy Loading Function
```javascript
const loadPolicies = async () => {
  const response = await axios.get(`${API_BASE_URL_POLICIES}/policies`);
  setAvailablePolicies(response.data.data);
  setShowPolicySelection(response.data.data.length > 0);
};
```

#### Enhanced Question Generation
```javascript
const handleGenerateQuestions = async () => {
  const requestData = {};
  if (!isAudit && selectedPolicyId) {
    requestData.policyId = selectedPolicyId;
  }
  const response = await axios.post(API_URL, requestData);
};
```

### Backend Changes (`jobs.py`)

#### New Request Model
```python
class QuestionGenerationRequest(BaseModel):
    policyId: Optional[str] = None
```

#### Enhanced Endpoint
```python
@router.post("/questions/{job_id}/{candidate_id}")
async def generate_interview_questions(
    job_id: int, 
    candidate_id: int, 
    generation_request: QuestionGenerationRequest = QuestionGenerationRequest()
):
```

#### Policy Loading Enhancement
```python
def load_policies(specific_policy_id: Optional[str] = None) -> str:
    if specific_policy_id:
        # Load only the specified policy
        policy_file = os.path.join(POLICIES_DIR, f"{specific_policy_id}.json")
        # ... load specific policy
    else:
        # Load all policies (existing behavior)
        # ... load all policies
```

## 🎨 UI/UX Features

### Visual Indicators
- **Dropdown Visibility**: Only shown for job interviews
- **Loading State**: Spinner while fetching policies
- **Selection Feedback**: Helper text explains impact
- **Seamless Integration**: Fits naturally into existing workflow

### Error Handling
- **Policy Load Failure**: Gracefully hides dropdown
- **No Policies Available**: Shows "All Available Policies" only
- **Invalid Policy Selection**: Falls back to all policies

## 📊 Benefits

### For Interviewers
- **Targeted Assessment**: Focus on specific policy areas
- **Customizable Scope**: Choose what to emphasize
- **Efficient Screening**: More relevant questions
- **Better Preparation**: Know which policy is being tested

### For Organizations
- **Compliance Focus**: Test specific regulatory requirements
- **Role Alignment**: Match questions to job-specific policies
- **Quality Control**: Ensure policy understanding
- **Audit Trail**: Track which policies were assessed

### For Candidates
- **Clear Expectations**: Understand which standards are being tested
- **Relevant Scenarios**: Face realistic work situations
- **Fair Assessment**: Evaluated on applicable policies only
- **Learning Opportunity**: Gain insight into company standards

## 🧪 Testing

### Manual Testing Steps
1. **Setup**: Create multiple policies in Policies Management
2. **Navigate**: Go to Manage section for a job candidate
3. **Verify**: Confirm policy dropdown appears (jobs only)
4. **Select**: Choose a specific policy
5. **Generate**: Click "Generate Questions" button
6. **Review**: Check that questions reflect selected policy

### Test Scenarios
- **No policies exist**: Dropdown hidden
- **Multiple policies exist**: All policies shown in dropdown
- **Policy selected**: Questions tailored to selection
- **No policy selected**: Questions use all policies
- **API failure**: Graceful degradation

### Test Script
```bash
cd backend
python test_policy_specific_questions.py
```

## 🚀 Future Enhancements

1. **Multi-Policy Selection**: Select multiple policies at once
2. **Policy Weighting**: Assign importance levels to different policies
3. **Policy Categories**: Group policies by type or department
4. **Question Preview**: Show sample questions for selected policy
5. **Policy Recommendations**: Suggest relevant policies based on job role
6. **Analytics**: Track which policies are most commonly selected

## 📝 Usage Instructions

### For Recruiters
1. Navigate to the Manage section for any job candidate
2. Notice the new "Select Policy for Question Generation" dropdown
3. Choose a specific policy to focus on, or leave blank for comprehensive coverage
4. Click "Generate Questions" to create tailored interview questions
5. Review the generated questions to see policy-specific content

### For System Administrators
1. Ensure policies are created in the Policies Management section
2. Policies will automatically appear in the dropdown for question generation
3. Monitor usage to understand which policies are most important for different roles

This feature provides granular control over interview question generation while maintaining the simplicity and effectiveness of the existing system.
