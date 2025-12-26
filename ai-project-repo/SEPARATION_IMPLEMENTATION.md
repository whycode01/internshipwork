# POLICY vs REPORT TEMPLATE SEPARATION - IMPLEMENTATION COMPLETE

## Overview
The system has been successfully updated to separate **Policies** from **Report Templates**, creating a clear two-step workflow:

1. **Policy → Question Generation**
2. **Report Template → Report Generation**

---

## Key Changes Made

### 1. Backend Changes

#### `/backend/routers/jobs.py`
- **Separated `load_policies()`**: Now only loads from `storage/policies/` directory
- **Added `load_report_template()`**: New function to load specific report templates
- **Updated `first_questions_prompt()`**: Simplified to use only policies for question generation
- **Enhanced `generate_report()`**: Now accepts `template_id` parameter for template-based reports
- **Added `template_based_report_prompt()`**: New function for template-specific report generation
- **Updated transcript endpoint**: Now accepts `template_id` query parameter

#### `/backend/storage/`
- **`storage/policies/`**: Contains interview policies for question generation
  - `technical_interview_policy_20250728_120000.json`
  - `customer_service_interview_policy_20250728_120001.json`
- **`storage/templates/`**: Contains report templates for report generation
  - `template_1_20250726_011702.json` (Technical Interview Assessment Report)
  - `template_2_20250726_021650.json` (Customer Service Representative Evaluation)

### 2. Frontend Changes

#### `/frontend/src/components/Manage.jsx`
- **Separated state management**: 
  - `availablePolicies` + `selectedPolicyId` for policies
  - `availableReportTemplates` + `selectedReportTemplateId` for report templates
- **Updated `loadPolicies()`**: Now loads policies and templates separately
- **Added dual selection UI**: 
  - Blue dropdown for policy selection (affects questions)
  - Green dropdown for report template selection (affects reports)
- **Updated transcript upload**: Passes `template_id` parameter to backend

---

## Workflow Description

### Step 1: Policy-Based Question Generation
```
User selects Policy → Backend generates questions based on policy guidelines
```
- **Purpose**: Tailor interview questions to company policies and standards
- **Storage**: `backend/storage/policies/*.json`
- **API Endpoint**: `POST /api/jobs/{job_id}/candidates/{candidate_id}/questions/?policy_id={id}`
- **UI**: Blue dropdown "Select Policy for Question Generation"

### Step 2: Template-Based Report Generation
```
User uploads transcript + selects Report Template → Backend generates report following template structure
```
- **Purpose**: Generate structured reports matching specific evaluation formats
- **Storage**: `backend/storage/templates/*.json`
- **API Endpoint**: `POST /api/jobs/transcript/{job_id}/{candidate_id}?template_id={id}`
- **UI**: Green dropdown "Select Report Template for Report Generation"

---

## API Endpoints

### Policies (for Question Generation)
- `GET /api/policies/policies` - List all policies
- `POST /api/policies/policies` - Create new policy

### Report Templates (for Report Generation)
- `GET /api/policies/report_templates` - List all report templates
- `POST /api/policies/report_templates` - Create new report template

### Question Generation
- `POST /api/jobs/{job_id}/candidates/{candidate_id}/questions/?policy_id={id}` - Generate questions with specific policy

### Report Generation
- `POST /api/jobs/transcript/{job_id}/{candidate_id}?template_id={id}` - Upload transcript and generate report with specific template

---

## User Interface

### Policy Selection (Question Generation)
```
┌─────────────────────────────────────────────┐
│ Select Policy for Question Generation       │
│ ┌─────────────────────────────────────────┐ │
│ │ [All Available Policies ▼]             │ │
│ │  - Technical Interview Policy           │ │
│ │  - Customer Service Interview Policy    │ │
│ └─────────────────────────────────────────┘ │
│ Questions will be tailored to the selected │
│ policy                                      │
└─────────────────────────────────────────────┘
```

### Report Template Selection (Report Generation)
```
┌─────────────────────────────────────────────┐
│ Select Report Template for Report Generation│
│ ┌─────────────────────────────────────────┐ │
│ │ [Default Report Format ▼]              │ │
│ │  - Technical Interview Assessment       │ │
│ │  - Customer Service Representative Eval │ │
│ └─────────────────────────────────────────┘ │
│ Report will follow the selected template   │
│ structure                                   │
└─────────────────────────────────────────────┘
```

---

## Benefits of Separation

1. **Clear Distinction**: Policies affect questions, templates affect reports
2. **Flexible Workflow**: Mix and match any policy with any template
3. **Better Organization**: Separate storage and management
4. **Improved UX**: Clear visual separation with different colors
5. **Scalable Architecture**: Easy to add new policies or templates independently

---

## Testing

Run the test script to verify the separation:
```bash
cd backend
python test_separated_workflow.py
```

This will verify:
- ✅ Policies are loaded separately from templates
- ✅ Question generation uses only policies
- ✅ Report generation uses only templates
- ✅ Clear workflow separation is maintained

---

## Summary

**BEFORE**: Mixed policies and templates in question generation
**AFTER**: Clean separation with distinct workflows

1. **Policies** → Control question content and interview focus
2. **Report Templates** → Control report structure and evaluation format

The system now provides a clear, separated workflow that allows users to independently control both the interview questions (via policies) and the final report format (via templates).
