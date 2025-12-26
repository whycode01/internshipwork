"""
Services for handling file operations and question processing
"""
import asyncio
import csv
import json
import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Use absolute imports when running as script, relative when as module
try:
    from .models import (PaginationInfo, Question, QuestionMetadata,
                         QuestionsListResponse, SearchParams)
except ImportError:
    from models import (PaginationInfo, Question, QuestionMetadata,
                        QuestionsListResponse, SearchParams)

logger = logging.getLogger(__name__)

class FileIndexService:
    """Service for indexing and managing CSV files"""
    
    def __init__(self, storage_path: str = "storage/jobs"):
        self.storage_path = Path(storage_path)
        self.file_index: Dict[str, Any] = {}
        self.last_updated: Optional[datetime] = None
        
    async def initialize_index(self):
        """Initialize the file index on startup"""
        await self.refresh_index()
        
    async def refresh_index(self):
        """Refresh the file index by scanning the storage directory"""
        logger.info(f"Refreshing file index from {self.storage_path}")
        
        if not self.storage_path.exists():
            logger.warning(f"Storage path {self.storage_path} does not exist")
            return
            
        index = {
            "files": {},
            "candidates": set(),
            "jobs": set(),
            "job_categories": set(),
            "last_updated": datetime.utcnow()
        }
        
        # Scan all directories and files
        for job_dir in self.storage_path.iterdir():
            if job_dir.is_dir():
                await self._index_job_directory(job_dir, index)
                
        # Convert sets to lists for serialization
        index["candidates"] = list(index["candidates"])
        index["jobs"] = list(index["jobs"])
        index["job_categories"] = list(index["job_categories"])
        
        self.file_index = index
        self.last_updated = index["last_updated"]
        logger.info(f"Index refreshed: {len(index['files'])} files, {len(index['candidates'])} candidates")
        
    async def _index_job_directory(self, job_dir: Path, index: Dict[str, Any]):
        """Index a single job directory"""
        # Parse job directory name: {job_id}_{job_category}
        dir_match = re.match(r"(\d+)_(.+)", job_dir.name)
        if not dir_match:
            logger.warning(f"Skipping directory with invalid format: {job_dir.name}")
            return
            
        job_id = int(dir_match.group(1))
        job_category = dir_match.group(2)
        
        index["jobs"].add(job_id)
        index["job_categories"].add(job_category)
        
        # Scan CSV files in the directory
        for csv_file in job_dir.glob("interview_questions_*.csv"):
            await self._index_csv_file(csv_file, job_id, job_category, index)
            
    async def _index_csv_file(self, csv_file: Path, job_id: int, job_category: str, index: Dict[str, Any]):
        """Index a single CSV file"""
        # Parse filename: interview_questions_{candidate_id}_{timestamp}.csv
        file_match = re.match(r"interview_questions_(\d+)_(\d{8}_\d{6})\.csv", csv_file.name)
        if not file_match:
            logger.warning(f"Skipping file with invalid format: {csv_file.name}")
            return
            
        candidate_id = int(file_match.group(1))
        timestamp_str = file_match.group(2)
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            logger.warning(f"Invalid timestamp format in file: {csv_file.name}")
            return
            
        # Get file stats
        stat = csv_file.stat()
        
        # Count questions in file
        question_count = await self._count_questions_in_file(csv_file)
        
        file_info = {
            "file_path": str(csv_file.relative_to(self.storage_path)),
            "absolute_path": str(csv_file),
            "candidate_id": candidate_id,
            "job_id": job_id,
            "job_category": job_category,
            "timestamp": timestamp,
            "file_size": stat.st_size,
            "question_count": question_count,
            "last_modified": datetime.fromtimestamp(stat.st_mtime)
        }
        
        # Create unique file key
        file_key = f"{candidate_id}_{job_id}_{timestamp_str}"
        index["files"][file_key] = file_info
        index["candidates"].add(candidate_id)
        
    async def _count_questions_in_file(self, csv_file: Path) -> int:
        """Count the number of questions in a CSV file"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                return sum(1 for row in reader if row and len(row) >= 3)
        except Exception as e:
            logger.error(f"Error counting questions in {csv_file}: {e}")
            return 0
            
    def get_files_by_candidate(self, candidate_id: int) -> List[Dict[str, Any]]:
        """Get all files for a specific candidate"""
        return [
            file_info for file_info in self.file_index.get("files", {}).values()
            if file_info["candidate_id"] == candidate_id
        ]
        
    def get_files_by_job(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all files for a specific job"""
        return [
            file_info for file_info in self.file_index.get("files", {}).values()
            if file_info["job_id"] == job_id
        ]
        
    def get_files_by_policy(self, policy_name: str) -> List[Dict[str, Any]]:
        """Get files by policy/job category (fuzzy matching)"""
        policy_lower = policy_name.lower()
        return [
            file_info for file_info in self.file_index.get("files", {}).values()
            if policy_lower in file_info["job_category"].lower()
        ]
        
    def get_files_by_candidate_and_job(self, candidate_id: int, job_id: int) -> List[Dict[str, Any]]:
        """Get files for specific candidate and job combination"""
        return [
            file_info for file_info in self.file_index.get("files", {}).values()
            if file_info["candidate_id"] == candidate_id and file_info["job_id"] == job_id
        ]
        
    async def get_index_info(self) -> Dict[str, Any]:
        """Get information about the current index"""
        return {
            "total_files": len(self.file_index.get("files", {})),
            "total_candidates": len(self.file_index.get("candidates", [])),
            "total_jobs": len(self.file_index.get("jobs", [])),
            "job_categories": self.file_index.get("job_categories", []),
            "last_updated": self.last_updated,
            "index_size": len(str(self.file_index))
        }

class QuestionService:
    """Service for processing and serving questions"""
    
    def __init__(self, file_index_service: FileIndexService):
        self.file_index_service = file_index_service
        self._question_cache: Dict[str, List[Question]] = {}
        
    async def get_questions_by_candidate(
        self, 
        candidate_id: int, 
        limit: int = 10, 
        offset: int = 0,
        question_type: Optional[str] = None,
        sort_by: str = "timestamp"
    ) -> QuestionsListResponse:
        """Get all questions for a candidate"""
        files = self.file_index_service.get_files_by_candidate(candidate_id)
        if not files:
            raise FileNotFoundError(f"No questions found for candidate {candidate_id}")
            
        # Sort files by timestamp (newest first)
        files.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Load questions from all files
        all_questions = []
        metadata = None
        
        for file_info in files:
            questions, file_metadata = await self._load_questions_from_file(file_info)
            if metadata is None:  # Use metadata from the first (newest) file
                metadata = file_metadata
            all_questions.extend(questions)
            
        # Apply filters
        if question_type:
            all_questions = [q for q in all_questions if q.question_type == question_type]
            
        # Apply sorting
        if sort_by == "question_type":
            all_questions.sort(key=lambda x: x.question_type)
        elif sort_by == "timestamp":
            pass  # Already sorted by file timestamp
            
        # Apply pagination
        total_items = len(all_questions)
        paginated_questions = all_questions[offset:offset + limit]
        
        pagination = self._create_pagination_info(offset, limit, total_items)
        
        return QuestionsListResponse(
            data={
                "metadata": metadata.dict() if metadata else {},
                "questions": [q.dict() for q in paginated_questions]
            },
            pagination=pagination
        )
        
    async def get_questions_by_candidate_and_job(
        self,
        candidate_id: int,
        job_id: int,
        limit: int = 10,
        offset: int = 0,
        question_type: Optional[str] = None
    ) -> QuestionsListResponse:
        """Get questions for specific candidate and job"""
        files = self.file_index_service.get_files_by_candidate_and_job(candidate_id, job_id)
        if not files:
            raise FileNotFoundError(f"No questions found for candidate {candidate_id} and job {job_id}")
            
        # Use the most recent file
        latest_file = max(files, key=lambda x: x["timestamp"])
        questions, metadata = await self._load_questions_from_file(latest_file)
        
        # Apply filters
        if question_type:
            questions = [q for q in questions if q.question_type == question_type]
            
        # Apply pagination
        total_items = len(questions)
        paginated_questions = questions[offset:offset + limit]
        
        pagination = self._create_pagination_info(offset, limit, total_items)
        
        return QuestionsListResponse(
            data={
                "metadata": metadata.dict(),
                "questions": [q.dict() for q in paginated_questions]
            },
            pagination=pagination
        )
        
    async def get_latest_questions_by_job(self, job_id: int, limit: int = 10) -> QuestionsListResponse:
        """Get the most recent questions for a job"""
        files = self.file_index_service.get_files_by_job(job_id)
        if not files:
            raise FileNotFoundError(f"No questions found for job {job_id}")
            
        # Get the most recent file
        latest_file = max(files, key=lambda x: x["timestamp"])
        questions, metadata = await self._load_questions_from_file(latest_file)
        
        # Limit questions
        limited_questions = questions[:limit]
        
        pagination = self._create_pagination_info(0, limit, len(questions))
        
        return QuestionsListResponse(
            data={
                "metadata": metadata.dict(),
                "questions": [q.dict() for q in limited_questions]
            },
            pagination=pagination
        )
        
    async def get_questions_by_policy(
        self,
        policy_name: str,
        limit: int = 10,
        offset: int = 0,
        question_type: Optional[str] = None
    ) -> QuestionsListResponse:
        """Get questions by policy/job category"""
        files = self.file_index_service.get_files_by_policy(policy_name)
        if not files:
            raise FileNotFoundError(f"No questions found for policy '{policy_name}'")
            
        # Sort by timestamp (newest first)
        files.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Load questions from files
        all_questions = []
        metadata = None
        
        for file_info in files:
            questions, file_metadata = await self._load_questions_from_file(file_info)
            if metadata is None:
                metadata = file_metadata
            all_questions.extend(questions)
            
        # Apply filters
        if question_type:
            all_questions = [q for q in all_questions if q.question_type == question_type]
            
        # Apply pagination
        total_items = len(all_questions)
        paginated_questions = all_questions[offset:offset + limit]
        
        pagination = self._create_pagination_info(offset, limit, total_items)
        
        return QuestionsListResponse(
            data={
                "metadata": metadata.dict() if metadata else {},
                "questions": [q.dict() for q in paginated_questions]
            },
            pagination=pagination
        )
        
    async def search_questions(self, search_params: SearchParams) -> QuestionsListResponse:
        """Advanced search for questions"""
        # Get relevant files based on search criteria
        all_files = list(self.file_index_service.file_index.get("files", {}).values())
        
        # Filter files based on criteria
        filtered_files = []
        for file_info in all_files:
            if search_params.candidate_id and file_info["candidate_id"] != search_params.candidate_id:
                continue
            if search_params.job_id and file_info["job_id"] != search_params.job_id:
                continue
            if search_params.policy_name and search_params.policy_name.lower() not in file_info["job_category"].lower():
                continue
            filtered_files.append(file_info)
            
        if not filtered_files:
            raise FileNotFoundError("No questions found matching search criteria")
            
        # Load questions from filtered files
        all_questions = []
        metadata = None
        
        for file_info in filtered_files:
            questions, file_metadata = await self._load_questions_from_file(file_info)
            if metadata is None:
                metadata = file_metadata
            all_questions.extend(questions)
            
        # Apply text search
        if search_params.query:
            query_lower = search_params.query.lower()
            all_questions = [
                q for q in all_questions 
                if query_lower in q.question_text.lower() or query_lower in q.objective.lower()
            ]
            
        # Apply question type filter
        if search_params.question_type:
            all_questions = [q for q in all_questions if q.question_type == search_params.question_type]
            
        # Apply sorting
        if search_params.sort_by == "question_type":
            all_questions.sort(key=lambda x: x.question_type)
            
        # Apply pagination
        total_items = len(all_questions)
        paginated_questions = all_questions[search_params.offset:search_params.offset + search_params.limit]
        
        pagination = self._create_pagination_info(search_params.offset, search_params.limit, total_items)
        
        return QuestionsListResponse(
            data={
                "search_params": search_params.dict(),
                "metadata": metadata.dict() if metadata else {},
                "questions": [q.dict() for q in paginated_questions]
            },
            pagination=pagination
        )
        
    async def _load_questions_from_file(self, file_info: Dict[str, Any]) -> Tuple[List[Question], QuestionMetadata]:
        """Load questions from a CSV file"""
        file_path = file_info["absolute_path"]
        
        # Check cache first
        cache_key = f"{file_info['candidate_id']}_{file_info['job_id']}_{file_info['timestamp']}"
        if cache_key in self._question_cache:
            questions = self._question_cache[cache_key]
        else:
            questions = await self._parse_csv_file(file_path)
            self._question_cache[cache_key] = questions
            
        # Create metadata
        metadata = QuestionMetadata(
            candidate_id=file_info["candidate_id"],
            job_id=file_info["job_id"],
            job_category=file_info["job_category"],
            policy_context=file_info["job_category"].replace("_", " ").title(),
            generated_at=file_info["timestamp"],
            source_file=file_info["file_path"],
            total_questions=len(questions)
        )
        
        return questions, metadata
        
    async def _parse_csv_file(self, file_path: str) -> List[Question]:
        """Parse CSV file and return list of Question objects"""
        questions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, 1):
                    if not row or len(row) < 3:
                        continue
                        
                    # Estimate difficulty and time based on question content
                    metadata = self._generate_question_metadata(row.get("question_text", ""))
                    
                    question = Question(
                        id=i,
                        question_text=row.get("question_text", "").strip('"'),
                        question_type=row.get("question_type", "Unknown"),
                        objective=row.get("objective", ""),
                        metadata=metadata
                    )
                    questions.append(question)
                    
        except Exception as e:
            logger.error(f"Error parsing CSV file {file_path}: {e}")
            raise
            
        return questions
        
    def _generate_question_metadata(self, question_text: str) -> Dict[str, Any]:
        """Generate metadata for a question based on its content"""
        metadata = {}
        
        # Estimate difficulty based on question complexity
        word_count = len(question_text.split())
        if word_count < 15:
            metadata["difficulty"] = "easy"
            metadata["estimated_time"] = "2-3 minutes"
        elif word_count < 30:
            metadata["difficulty"] = "intermediate"
            metadata["estimated_time"] = "5-7 minutes"
        else:
            metadata["difficulty"] = "advanced"
            metadata["estimated_time"] = "8-10 minutes"
            
        # Extract skills from question content
        skills = []
        skill_keywords = {
            "analysis": ["analyze", "analysis", "analytical"],
            "communication": ["communicate", "present", "explain"],
            "leadership": ["lead", "manage", "team"],
            "problem_solving": ["solve", "problem", "challenge"],
            "technical": ["technical", "system", "develop"],
            "data": ["data", "dataset", "information"]
        }
        
        text_lower = question_text.lower()
        for skill, keywords in skill_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                skills.append(skill)
                
        if skills:
            metadata["skills_assessed"] = skills
            
        return metadata
        
    def _create_pagination_info(self, offset: int, limit: int, total_items: int) -> PaginationInfo:
        """Create pagination information"""
        current_page = (offset // limit) + 1
        total_pages = (total_items + limit - 1) // limit
        
        return PaginationInfo(
            current_page=current_page,
            total_pages=total_pages,
            total_items=total_items,
            items_per_page=limit,
            has_next=offset + limit < total_items,
            has_previous=offset > 0
        )
