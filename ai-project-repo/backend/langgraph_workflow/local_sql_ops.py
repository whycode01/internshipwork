"""
Local SQL operations and LLM integration for LangGraph workflow.
Contains patched versions that handle None request objects.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

logger = logging.getLogger(__name__)

# Global thread pool executor for cases where request is None
_global_executor = None

def get_global_executor():
    """Get or create global thread pool executor."""
    global _global_executor
    if _global_executor is None:
        _global_executor = ThreadPoolExecutor(max_workers=4)
    return _global_executor

def call_model(user_message):
    """Call the LLM model synchronously."""
    try:
        # Import settings service from the parent directory
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        
        from routers.config import settings_service
        
        llm = settings_service.get_cached_llm()
        response = llm.invoke(user_message)
        return response
    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        return f"Error: {str(e)}"

async def async_call_model(prompt: str, request=None) -> str:
    """
    Async wrapper for calling the LLM model from agents.
    Handles both FastAPI Request objects and None cases.
    """
    try:
        loop = asyncio.get_event_loop()
        
        # Check if we have a proper request with executor
        if request and hasattr(request, 'app') and hasattr(request.app, 'state') and hasattr(request.app.state, 'executor'):
            executor = request.app.state.executor
        else:
            # Fallback to global executor for cases where request is None or incomplete
            executor = get_global_executor()
            if request is None:
                logger.debug("Using global executor due to None request")
        
        # Run the model call in executor
        response = await loop.run_in_executor(executor, call_model, prompt)
        return str(response)
        
    except Exception as e:
        logger.error(f"Async model call failed: {str(e)}")
        return f"Error calling model: {str(e)}"