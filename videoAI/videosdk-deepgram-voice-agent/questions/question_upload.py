"""
File upload utility for question transcripts
Handles markdown file upload and validation
"""
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to import question_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from questions.question_manager import Question, QuestionParser


class QuestionFileManager:
    """Manage question file uploads and storage"""
    
    def __init__(self, upload_dir: str = "questions"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.current_questions_file = None
        self.parsed_questions: List[Question] = []
    
    def upload_questions_file(self, file_path: str, filename: Optional[str] = None) -> bool:
        """Upload and validate questions file"""
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
            
            # Validate file extension
            if not file_path.lower().endswith(('.md', '.markdown', '.txt')):
                print("Only Markdown (.md, .markdown) and text (.txt) files are supported")
                return False
            
            # Generate filename if not provided
            if not filename:
                filename = Path(file_path).name
            
            # Check if file is already in the target directory
            destination = self.upload_dir / filename
            source_path = Path(file_path).resolve()
            dest_path = destination.resolve()
            
            if source_path != dest_path:
                # Copy file to upload directory only if it's not already there
                shutil.copy2(file_path, destination)
            else:
                # File is already in the target directory, use it directly
                destination = source_path
            
            # Parse and validate questions
            questions = self._parse_and_validate(destination)
            if not questions:
                print("No valid questions found in file")
                return False
            
            # Store successful upload
            self.current_questions_file = destination
            self.parsed_questions = questions
            
            print(f"Successfully uploaded {len(questions)} questions from {filename}")
            return True
            
        except Exception as e:
            print(f"Error uploading file: {e}")
            return False
    
    def _parse_and_validate(self, file_path: Path) -> List[Question]:
        """Parse and validate questions from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            parser = QuestionParser()
            questions = parser.parse_markdown(content)
            
            # Validate questions
            valid_questions = []
            for q in questions:
                if self._validate_question(q):
                    valid_questions.append(q)
                else:
                    print(f"Skipping invalid question: {q.id}")
            
            return valid_questions
            
        except Exception as e:
            print(f"Error parsing file: {e}")
            return []
    
    def _validate_question(self, question: Question) -> bool:
        """Validate individual question"""
        # Check required fields
        if not question.text or len(question.text.strip()) < 10:
            return False
        
        if not question.id:
            return False
        
        return True
    
    def get_current_questions(self) -> List[Question]:
        """Get currently loaded questions"""
        return self.parsed_questions
    
    def clear_questions(self):
        """Clear current questions"""
        self.current_questions_file = None
        self.parsed_questions = []
    
    def list_uploaded_files(self) -> List[str]:
        """List all uploaded question files"""
        try:
            files = []
            for file_path in self.upload_dir.glob("*.md"):
                files.append(file_path.name)
            for file_path in self.upload_dir.glob("*.txt"):
                files.append(file_path.name)
            return sorted(files)
        except Exception:
            return []
    
    def load_existing_file(self, filename: str) -> bool:
        """Load questions from existing uploaded file"""
        file_path = self.upload_dir / filename
        if file_path.exists():
            questions = self._parse_and_validate(file_path)
            if questions:
                self.current_questions_file = file_path
                self.parsed_questions = questions
                print(f"Loaded {len(questions)} questions from {filename}")
                return True
        
        print(f"Failed to load questions from {filename}")
        return False
    
    def get_questions_summary(self) -> dict:
        """Get summary of loaded questions"""
        if not self.parsed_questions:
            return {"total": 0, "categories": {}, "difficulties": {}}
        
        summary = {
            "total": len(self.parsed_questions),
            "categories": {},
            "difficulties": {},
            "file": self.current_questions_file.name if self.current_questions_file else "None"
        }
        
        # Count by category
        for q in self.parsed_questions:
            cat = q.category.value
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1
        
        # Count by difficulty
        for q in self.parsed_questions:
            diff = q.difficulty.value
            summary["difficulties"][diff] = summary["difficulties"].get(diff, 0) + 1
        
        return summary

# Simple CLI for testing
def main():
    """Simple CLI for testing file upload"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python question_upload.py <markdown_file_path>")
        return
    
    file_path = sys.argv[1]
    manager = QuestionFileManager()
    
    if manager.upload_questions_file(file_path):
        summary = manager.get_questions_summary()
        print(f"\nUpload Summary:")
        print(f"Total questions: {summary['total']}")
        print(f"Categories: {summary['categories']}")
        print(f"Difficulties: {summary['difficulties']}")
        
        print(f"\nFirst few questions:")
        for i, q in enumerate(manager.get_current_questions()[:3]):
            print(f"{i+1}. [{q.category.value}] {q.text[:100]}...")
    else:
        print("Failed to upload questions file")

if __name__ == "__main__":
    main()
