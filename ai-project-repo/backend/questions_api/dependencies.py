"""
Dependency injection for FastAPI services
"""
from functools import lru_cache

# Use absolute imports when running as script, relative when as module
try:
    from .config import settings
    from .services import FileIndexService, QuestionService
except ImportError:
    from config import settings
    from services import FileIndexService, QuestionService

# Global service instances
_file_index_service: FileIndexService = None
_question_service: QuestionService = None

@lru_cache()
def get_file_index_service() -> FileIndexService:
    """Get or create FileIndexService instance"""
    global _file_index_service
    if _file_index_service is None:
        _file_index_service = FileIndexService(settings.storage_path)
    return _file_index_service

@lru_cache()
def get_question_service() -> QuestionService:
    """Get or create QuestionService instance"""
    global _question_service
    if _question_service is None:
        file_index_service = get_file_index_service()
        _question_service = QuestionService(file_index_service)
    return _question_service
