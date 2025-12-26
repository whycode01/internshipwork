"""
Workflows package for AI project

This package contains LangGraph-based workflows for question generation.
"""

# Version information
__version__ = "1.0.0"
__author__ = "AI Assistant"

# Import main workflow functions for easy access
try:
    from .simple_workflow import execute_question_generation_workflow_simple
    
    __all__ = [
        'execute_question_generation_workflow_simple'
    ]
except ImportError:
    # Handle import errors gracefully
    __all__ = []
