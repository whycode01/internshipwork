# LangGraph Question Generation Workflow Documentation

## Overview

This document describes the LangGraph-based question generation workflow implemented to enhance the interview question generation process. The workflow replaces the previous single-step approach with a modular, robust, and extensible system.

## Architecture

### Previous Approach
- Single function with linear execution
- Minimal error handling
- Limited validation
- Difficult to extend or modify

### New LangGraph Approach
- Modular workflow with distinct nodes
- Comprehensive error handling and retry logic
- Built-in validation and quality assurance
- Easy to extend with new features
- Better monitoring and debugging capabilities

## Workflow Components

### 1. State Management
The workflow uses a `QuestionGenerationState` TypedDict to maintain state across all nodes:

```python
class QuestionGenerationState(TypedDict):
    # Input data
    job_id: int
    candidate_id: int
    job: Dict[str, Any]
    candidate: Dict[str, Any]
    request: Any
    specific_policy_id: Optional[str]
    
    # Intermediate state
    policies: Optional[str]
    prompt: Optional[str]
    llm_response: Optional[Any]
    # ... additional state fields
```

### 2. Workflow Nodes

#### Node 1: Data Gathering (`gather_data_node`)
- **Purpose**: Collect and validate input data
- **Operations**:
  - Load company policies (specific or all)
  - Validate job and candidate information
  - Update candidate status
- **Error Handling**: Catches data loading errors and sets error state

#### Node 2: Prompt Construction (`build_prompt_node`)
- **Purpose**: Build optimized prompts for question generation
- **Operations**:
  - Extract job and candidate details
  - Process resume and skills information
  - Integrate company policies
  - Construct policy-enhanced prompt
- **Error Handling**: Handles prompt construction failures

#### Node 3: LLM Interaction (`call_llm_node`)
- **Purpose**: Execute language model calls with async handling
- **Operations**:
  - Get cached LLM instance
  - Execute prompt in thread pool to prevent blocking
  - Handle various response formats
- **Error Handling**: Retry mechanism for transient failures

#### Node 4: Response Parsing (`parse_response_node`)
- **Purpose**: Extract and parse JSON content from LLM responses
- **Operations**:
  - Extract content from various response formats
  - Clean markdown code blocks
  - Parse JSON arrays
  - Validate JSON structure
- **Error Handling**: Detailed JSON parsing error messages with retry

#### Node 5: Question Validation (`validate_questions_node`)
- **Purpose**: Ensure question quality and completeness
- **Operations**:
  - Check question count (minimum 8, target 12)
  - Validate required fields
  - Check question diversity
  - Assess content quality
- **Error Handling**: Detailed validation errors with retry capability

#### Node 6: Question Persistence (`save_questions_node`)
- **Purpose**: Save validated questions to file system
- **Operations**:
  - Convert to pandas DataFrame
  - Generate timestamped filename
  - Save to CSV format
  - Update candidate status
- **Error Handling**: File system error handling

#### Node 7: Retry Management (`retry_node`)
- **Purpose**: Handle retry logic for failed operations
- **Operations**:
  - Track retry count (max 2 retries)
  - Determine retry target based on failure type
  - Update status and reset error flags
- **Error Handling**: Prevents infinite retry loops

#### Node 8: Error Handling (`error_handler_node`)
- **Purpose**: Centralized error handling and cleanup
- **Operations**:
  - Log error details
  - Update candidate status
  - Prepare final error state
- **Error Handling**: Ensures graceful failure handling

### 3. Routing Logic

#### Conditional Routing Functions
- `route_after_llm()`: Routes after LLM call based on success/failure
- `route_after_parsing()`: Routes after response parsing
- `route_after_validation()`: Routes after question validation
- `route_after_retry()`: Determines what to retry based on failure type

#### Decision Logic
```python
def route_after_validation(state: QuestionGenerationState) -> str:
    if state.get('status') == 'questions_validated':
        return "save_questions"
    elif state.get('should_retry', False):
        return should_retry(state)
    else:
        return "error_handler"
```

## Enhanced Features

### 1. Validation System
The new workflow includes comprehensive validation:

```python
def validate_questions(questions_data: List[Dict]) -> ValidationResult:
    # Check question count
    # Validate required fields
    # Check question type diversity
    # Assess content quality
    # Return detailed validation results
```

**Validation Criteria**:
- Minimum 8 questions, target 12
- Required fields: `question_text`, `question_type`, `objective`
- Valid question types: Behavioral, Technical, Situational, etc.
- Content length validation
- Question type diversity assessment

### 2. Retry Mechanism
- **Max Retries**: 2 attempts
- **Retry Targets**: Determined by failure type
  - JSON parsing errors → Retry from LLM call
  - Other errors → Retry from prompt building
- **Status Tracking**: Clear retry count and status updates

### 3. Error Handling
- **Granular Error Types**: Specific error messages for different failure modes
- **Fallback Support**: Automatic fallback to original method if workflow fails
- **Status Updates**: Real-time candidate status updates throughout process

### 4. Monitoring and Logging
```python
print(f"DEBUG: Gathering data for job {state['job_id']}, candidate {state['candidate_id']}")
print(f"DEBUG: Successfully parsed {len(questions_data)} questions")
print(f"ERROR: JSON parsing error: {str(e)}")
```

## Integration Points

### 1. API Endpoint Integration
The workflow is integrated into the existing API endpoint:

```python
@router.post("/questions/{job_id}/{candidate_id}")
async def generate_interview_questions(...):
    # Start Background Task For Question Generation with LangGraph workflow
    background_tasks.add_task(
        generate_first_questions,  # Now uses LangGraph
        job_id, candidate_id, job, candidate, request, 
        generation_request.policyId
    )
```

### 2. Fallback Mechanism
```python
async def generate_first_questions(...):
    try:
        # Execute LangGraph workflow
        result = await execute_question_generation_workflow(...)
    except Exception as e:
        # Fallback to original method
        await generate_first_questions_fallback(...)
```

### 3. Database Integration
- Uses existing `update_candidate()` function for status updates
- Maintains compatibility with existing file storage structure
- Preserves CSV output format for frontend compatibility

## Benefits

### 1. Improved Reliability
- **Retry Logic**: Automatic retries for transient failures
- **Validation**: Quality assurance before saving questions
- **Fallback**: Graceful degradation if workflow fails

### 2. Better Monitoring
- **Status Tracking**: Real-time updates on workflow progress
- **Detailed Logging**: Comprehensive logging for debugging
- **Error Reporting**: Clear error messages and failure reasons

### 3. Enhanced Extensibility
- **Modular Design**: Easy to add new validation rules
- **Node Addition**: Simple to add new processing steps
- **Custom Routing**: Flexible routing logic for complex scenarios

### 4. Quality Assurance
- **Question Validation**: Ensures generated questions meet quality standards
- **Content Checking**: Validates question length, type diversity
- **Error Prevention**: Catches issues before they reach the user

## Usage Examples

### 1. Basic Usage
```python
# Execute workflow with default settings
result = await execute_question_generation_workflow(
    job_id=1,
    candidate_id=1,
    job=job_data,
    candidate=candidate_data,
    request=request_obj
)
```

### 2. With Specific Policy
```python
# Execute workflow with specific policy
result = await execute_question_generation_workflow(
    job_id=1,
    candidate_id=1,
    job=job_data,
    candidate=candidate_data,
    request=request_obj,
    specific_policy_id="policy_123"
)
```

### 3. Result Handling
```python
if result["success"]:
    print(f"Generated {result['questions_count']} questions")
    print(f"Saved to: {result['questions_file_path']}")
else:
    print(f"Failed: {result['error_message']}")
    print(f"Retries attempted: {result['retry_count']}")
```

## Configuration

### 1. Retry Settings
```python
# Maximum number of retries
MAX_RETRIES = 2

# Retry conditions
def should_retry(state: QuestionGenerationState) -> str:
    return state.get('should_retry', False) and state.get('retry_count', 0) < MAX_RETRIES
```

### 2. Validation Settings
```python
# Minimum questions required
MIN_QUESTIONS = 8
TARGET_QUESTIONS = 12

# Valid question types
VALID_QUESTION_TYPES = [
    'Behavioral', 'Technical', 'Situational', 
    'Policy/Compliance', 'Cultural Fit', 'Gap Analysis', 'Curveball'
]
```

## Testing and Debugging

### 1. Debug Mode
Enable detailed logging by setting debug flags:
```python
DEBUG_MODE = True  # Enable detailed logging
VERBOSE_VALIDATION = True  # Show validation details
```

### 2. State Inspection
The workflow state can be inspected at any point:
```python
def debug_state(state: QuestionGenerationState):
    print(f"Current status: {state.get('status')}")
    print(f"Retry count: {state.get('retry_count', 0)}")
    print(f"Error message: {state.get('error_message')}")
```

### 3. Testing Individual Nodes
Each node can be tested independently:
```python
# Test data gathering
test_state = {...}
result_state = gather_data_node(test_state)
assert result_state['status'] == 'data_gathered'
```

## Future Extensions

### 1. Multi-Model Support
Add support for using multiple LLMs:
```python
# Add model selection node
workflow.add_node("select_model", model_selection_node)
```

### 2. Question Enhancement
Add question improvement nodes:
```python
# Add question enhancement
workflow.add_node("enhance_questions", question_enhancement_node)
```

### 3. A/B Testing
Add experimental question generation paths:
```python
# Add experimental path
workflow.add_conditional_edges(
    "build_prompt",
    experiment_router,
    {"experimental": "experimental_prompt", "standard": "call_llm"}
)
```

### 4. Real-time Feedback
Add feedback incorporation:
```python
# Add feedback processing
workflow.add_node("process_feedback", feedback_processing_node)
```

## Maintenance

### 1. Regular Updates
- Update validation rules as requirements change
- Add new question types as needed
- Enhance error handling based on observed failures

### 2. Performance Monitoring
- Monitor workflow execution times
- Track retry rates and failure patterns
- Optimize bottleneck nodes

### 3. Version Management
- Use semantic versioning for workflow changes
- Maintain backward compatibility
- Document breaking changes

## Conclusion

The LangGraph-based question generation workflow provides a robust, extensible, and maintainable solution for generating interview questions. It addresses the limitations of the previous approach while providing a foundation for future enhancements.

Key benefits include:
- **Reliability**: Comprehensive error handling and retry logic
- **Quality**: Built-in validation and quality assurance
- **Extensibility**: Modular design for easy enhancement
- **Monitoring**: Detailed logging and status tracking
- **Maintainability**: Clear separation of concerns and documentation

The workflow is production-ready and includes fallback mechanisms to ensure system reliability during the transition period.
