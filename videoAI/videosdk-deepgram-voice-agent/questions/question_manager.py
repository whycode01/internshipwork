"""
Question management system for AI interviewer
Handles parsing, storage, and retrieval of interview questions
"""
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class QuestionCategory(Enum):
    INTRODUCTION = "introduction"
    TECHNICAL = "technical"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    CLOSING = "closing"

class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class Question:
    """Canonical question object"""
    id: str
    text: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    expected_keywords: List[str]
    time_limit_minutes: Optional[int] = None
    follow_up_template: Optional[str] = None
    metadata: Optional[Dict] = None

class QuestionParser:
    """Parse questions from Markdown files"""
    
    def __init__(self):
        self.questions: List[Question] = []
        self.current_category = QuestionCategory.TECHNICAL
        self.current_difficulty = DifficultyLevel.MEDIUM
    
    def parse_markdown(self, markdown_content: str) -> List[Question]:
        """Parse questions from markdown content"""
        self.questions = []
        lines = markdown_content.split('\n')
        
        current_question = None
        question_text = ""
        question_id = 1
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Parse category headers
            if line.startswith('# ') or line.startswith('## '):
                self._parse_category_header(line)
                continue
            
            # Parse difficulty indicators
            if line.startswith('**Difficulty:'):
                self._parse_difficulty(line)
                continue
            
            # Parse question markers
            if line.startswith('**Q') or line.startswith('Q') or line.startswith('-'):
                # Save previous question if exists
                if current_question and question_text:
                    current_question.text = question_text.strip()
                    self.questions.append(current_question)
                
                # Start new question
                question_text = self._extract_question_text(line)
                current_question = Question(
                    id=f"q_{question_id}",
                    text="",
                    category=self.current_category,
                    difficulty=self.current_difficulty,
                    expected_keywords=[]
                )
                question_id += 1
            
            # Parse expected keywords
            elif line.startswith('*Keywords:') or line.startswith('*Expected:'):
                if current_question:
                    keywords = self._extract_keywords(line)
                    current_question.expected_keywords = keywords
            
            # Parse time limit
            elif line.startswith('*Time:') or line.startswith('*Duration:'):
                if current_question:
                    time_limit = self._extract_time_limit(line)
                    current_question.time_limit_minutes = time_limit
            
            # Parse follow-up template
            elif line.startswith('*Follow-up:'):
                if current_question:
                    follow_up = self._extract_follow_up(line)
                    current_question.follow_up_template = follow_up
            
            # Continue question text
            elif current_question and question_text:
                question_text += " " + line
        
        # Save last question
        if current_question and question_text:
            current_question.text = question_text.strip()
            self.questions.append(current_question)
        
        return self.questions
    
    def _parse_category_header(self, line: str):
        """Parse category from header"""
        header = line.replace('#', '').strip().lower()
        
        if 'introduction' in header or 'intro' in header:
            self.current_category = QuestionCategory.INTRODUCTION
        elif 'coding' in header or 'algorithm' in header:
            self.current_category = QuestionCategory.CODING
        elif 'system' in header or 'design' in header:
            self.current_category = QuestionCategory.SYSTEM_DESIGN
        elif 'behavioral' in header or 'behaviour' in header:
            self.current_category = QuestionCategory.BEHAVIORAL
        elif 'closing' in header or 'conclusion' in header:
            self.current_category = QuestionCategory.CLOSING
        else:
            self.current_category = QuestionCategory.TECHNICAL
    
    def _parse_difficulty(self, line: str):
        """Parse difficulty level"""
        difficulty_text = line.lower()
        if 'easy' in difficulty_text:
            self.current_difficulty = DifficultyLevel.EASY
        elif 'hard' in difficulty_text:
            self.current_difficulty = DifficultyLevel.HARD
        else:
            self.current_difficulty = DifficultyLevel.MEDIUM
    
    def _extract_question_text(self, line: str) -> str:
        """Extract question text from line"""
        # Remove question markers and formatting
        text = re.sub(r'^\*\*Q\d+[\):\.]?\*\*', '', line)
        text = re.sub(r'^Q\d+[\):\.]?', '', text)
        text = re.sub(r'^-\s*', '', text)
        text = re.sub(r'^\*\*', '', text)
        text = re.sub(r'\*\*$', '', text)
        return text.strip()
    
    def _extract_keywords(self, line: str) -> List[str]:
        """Extract keywords from line"""
        text = re.sub(r'^\*Keywords?:', '', line, flags=re.IGNORECASE)
        text = re.sub(r'^\*Expected:', '', text, flags=re.IGNORECASE)
        keywords = [k.strip() for k in text.split(',')]
        return [k for k in keywords if k]
    
    def _extract_time_limit(self, line: str) -> Optional[int]:
        """Extract time limit in minutes"""
        numbers = re.findall(r'\d+', line)
        return int(numbers[0]) if numbers else None
    
    def _extract_follow_up(self, line: str) -> str:
        """Extract follow-up template"""
        text = re.sub(r'^\*Follow-up:', '', line, flags=re.IGNORECASE)
        return text.strip()

class QuestionManager:
    """Manage questions during interview"""
    
    def __init__(self, questions: List[Question]):
        self.questions = questions
        self.current_index = 0
        self.asked_questions = []
        self.candidate_answers = []
    
    def get_current_question(self) -> Optional[Question]:
        """Get current question to ask"""
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None
    
    def mark_question_asked(self, answer: str = ""):
        """Mark current question as asked and move to next"""
        if self.current_index < len(self.questions):
            current_q = self.questions[self.current_index]
            self.asked_questions.append(current_q)
            self.candidate_answers.append(answer)
            self.current_index += 1
    
    def get_progress(self) -> Dict:
        """Get interview progress"""
        return {
            "total_questions": len(self.questions),
            "asked_questions": len(self.asked_questions),
            "remaining_questions": len(self.questions) - len(self.asked_questions),
            "progress_percentage": (len(self.asked_questions) / len(self.questions)) * 100 if self.questions else 0
        }
    
    def get_context_summary(self) -> str:
        """Get summary of interview context for LLM"""
        if not self.asked_questions:
            return "Interview just started."
        
        summary = f"Interview progress: {len(self.asked_questions)}/{len(self.questions)} questions asked.\n"
        summary += f"Current category: {self.get_current_question().category.value if self.get_current_question() else 'Complete'}\n"
        
        # Add last few Q&A for context
        recent_qa = []
        for i in range(max(0, len(self.asked_questions) - 3), len(self.asked_questions)):
            q = self.asked_questions[i]
            a = self.candidate_answers[i] if i < len(self.candidate_answers) else "No answer"
            recent_qa.append(f"Q: {q.text[:100]}... A: {a[:100]}...")
        
        if recent_qa:
            summary += "Recent Q&A:\n" + "\n".join(recent_qa)
        
        return summary

def load_questions_from_file(file_path: str) -> List[Question]:
    """Load questions from markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parser = QuestionParser()
        questions = parser.parse_markdown(content)
        
        print(f"Loaded {len(questions)} questions from {file_path}")
        return questions
    
    except Exception as e:
        print(f"Error loading questions from {file_path}: {e}")
        return []
