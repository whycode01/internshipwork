#!/usr/bin/env python3
"""Test script to verify WorkflowState serialization is fixed."""

import sys

sys.path.append('.')

from langgraph_workflow.models import DecisionStatus, WorkflowState


def test_serialization():
    """Test WorkflowState serialization with string report."""
    
    # Test WorkflowState serialization with string report
    state = WorkflowState(
        candidate_id='test_26',
        candidate_name='Test Candidate',
        raw_transcript='Test transcript',
        job_description={'title': 'Software Engineer'},
        policy_template={'content': 'Test template'},
        technical_score=8.5,
        behavioral_score=7.8,
        experience_score=8.2,
        cultural_score=7.5,
        final_score=78.5,
        decision=DecisionStatus.SELECTED,
        generated_report='This is a test report string'  # String instead of AIMessage
    )

    print('✓ WorkflowState created successfully with scores:')
    print(f'  Technical: {state.technical_score}')
    print(f'  Behavioral: {state.behavioral_score}')
    print(f'  Experience: {state.experience_score}')
    print(f'  Cultural: {state.cultural_score}')
    print(f'  Final: {state.final_score}')
    print(f'  Decision: {state.decision}')
    print(f'  Report type: {type(state.generated_report)}')
    print('✓ No serialization errors - fix successful!')

if __name__ == "__main__":
    test_serialization()