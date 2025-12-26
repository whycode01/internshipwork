#!/usr/bin/env python3
"""
Transcript Manager
Handles recording and storage of interview transcripts
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class TranscriptEntry:
    """Single entry in the interview transcript"""
    speaker: str
    message: str
    timestamp: str
    duration_seconds: float
    confidence: Optional[float] = None
    message_type: str = "speech"  # speech, system, action

@dataclass
class Transcript:
    interview_id: str
    meeting_id: str
    start_time: str
    job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    end_time: Optional[str] = None
    duration_total: float = 0.0
    participants: Optional[List[str]] = None
    entries: Optional[List[TranscriptEntry]] = None
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        if self.entries is None:
            self.entries = []
        if self.participants is None:
            self.participants = []
        if self.metadata is None:
            self.metadata = {}

class TranscriptManager:
    """Manages transcript recording and storage"""
    
    def __init__(self, storage_dir: str = "transcripts"):
        self.storage_dir = storage_dir
        self.transcripts_dir = storage_dir  # Add this attribute for consistency
        self.current_transcript: Optional[Transcript] = None
        self.start_time: Optional[datetime] = None
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
    
    def start_recording(self, meeting_id: str, job_id: str = None, candidate_id: str = None, participants: List[str] = None, metadata: Dict = None) -> str:
        """Start recording a new interview transcript"""
        interview_id = str(uuid.uuid4())
        self.start_time = datetime.now(timezone.utc)
        
        self.current_transcript = Transcript(
            interview_id=interview_id,
            meeting_id=meeting_id,
            job_id=job_id,
            candidate_id=candidate_id,
            start_time=self.start_time.isoformat(),
            participants=participants or [],
            metadata=metadata or {}
        )
        
        # Add start entry
        self.add_entry("System", "Interview started", message_type="system")
        
        print(f"📝 Started recording transcript for interview {interview_id}")
        if job_id and candidate_id:
            print(f"📝 Job ID: {job_id}, Candidate ID: {candidate_id}")
        return interview_id
    
    def add_entry(self, speaker: str, message: str, confidence: float = None, message_type: str = "speech"):
        """Add an entry to the current transcript"""
        if not self.current_transcript:
            print("⚠️ No active transcript recording")
            return
        
        current_time = datetime.now(timezone.utc)
        duration = (current_time - self.start_time).total_seconds() if self.start_time else 0
        
        entry = TranscriptEntry(
            speaker=speaker,
            message=message,
            timestamp=current_time.strftime("%H:%M:%S"),
            duration_seconds=duration,
            confidence=confidence,
            message_type=message_type
        )
        
        self.current_transcript.entries.append(entry)
        print(f"📝 Added to transcript [{entry.timestamp}] {speaker}: {message[:50]}...")
    
    def add_participant(self, participant_name: str):
        """Add a participant to the current transcript"""
        if self.current_transcript and participant_name not in self.current_transcript.participants:
            self.current_transcript.participants.append(participant_name)
            self.add_entry("System", f"{participant_name} joined the interview", message_type="system")
    
    def end_recording(self) -> Optional[str]:
        """End the current transcript recording and save to file"""
        if not self.current_transcript:
            print("⚠️ No active transcript to end")
            return None
        
        # Add end entry
        self.add_entry("System", "Interview ended", message_type="system")
        
        # Calculate total duration
        end_time = datetime.now(timezone.utc)
        self.current_transcript.end_time = end_time.isoformat()
        if self.start_time:
            self.current_transcript.duration_total = (end_time - self.start_time).total_seconds()
        
        # Save to file
        filename = self.save_transcript(self.current_transcript)
        
        # Reset current transcript
        interview_id = self.current_transcript.interview_id
        self.current_transcript = None
        self.start_time = None
        
        print(f"📝 Ended recording transcript for interview {interview_id}")
        return filename
    
    def _get_storage_path(self, job_id: str = None, candidate_id: str = None) -> str:
        """Get the appropriate storage path based on job_id and candidate_id"""
        if job_id and candidate_id:
            # Organized by job and candidate: transcripts/job-5/candidate-24/
            # Clean the IDs by removing existing prefixes if present
            clean_job_id = job_id.replace("job-", "") if job_id.startswith("job-") else job_id
            clean_candidate_id = candidate_id.replace("candidate-", "") if candidate_id.startswith("candidate-") else candidate_id
            
            job_dir = f"job-{clean_job_id}"
            candidate_dir = f"candidate-{clean_candidate_id}"
            storage_path = os.path.join(self.storage_dir, job_dir, candidate_dir)
        elif job_id:
            # Organized by job only: transcripts/job-5/
            clean_job_id = job_id.replace("job-", "") if job_id.startswith("job-") else job_id
            job_dir = f"job-{clean_job_id}"
            storage_path = os.path.join(self.storage_dir, job_dir)
        else:
            # Default storage: transcripts/
            storage_path = self.storage_dir
        
        # Create directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        return storage_path

    def save_transcript(self, transcript: Transcript) -> str:
        """Save transcript to JSON file with organized folder structure"""
        # Generate filename with job and candidate info if available
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        if transcript.job_id and transcript.candidate_id:
            filename = f"interview-{transcript.job_id}-{transcript.candidate_id}-{timestamp}.json"
        elif transcript.job_id:
            filename = f"interview-{transcript.job_id}-{timestamp}.json"
        else:
            filename = f"interview-{transcript.interview_id}-{timestamp}.json"
        
        # Get appropriate storage path
        storage_path = self._get_storage_path(transcript.job_id, transcript.candidate_id)
        filepath = os.path.join(storage_path, filename)
        
        # Convert to dict for JSON serialization
        transcript_dict = asdict(transcript)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(transcript_dict, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved transcript to {filepath}")
        return filename
    
    def generate_text_transcript(self, transcript: Transcript = None) -> str:
        """Generate a human-readable text version of the transcript"""
        if not transcript:
            transcript = self.current_transcript
        
        if not transcript:
            return "No transcript available"
        
        lines = []
        lines.append("INTERVIEW TRANSCRIPT")
        lines.append("=" * 50)
        lines.append(f"Interview ID: {transcript.interview_id}")
        lines.append(f"Meeting ID: {transcript.meeting_id}")
        lines.append(f"Start Time: {transcript.start_time}")
        if transcript.end_time:
            lines.append(f"End Time: {transcript.end_time}")
            lines.append(f"Duration: {transcript.duration_total:.1f} seconds")
        lines.append(f"Participants: {', '.join(transcript.participants)}")
        lines.append("")
        lines.append("CONVERSATION:")
        lines.append("-" * 50)
        
        for entry in transcript.entries:
            if entry.message_type == "speech":
                duration_str = f"[{int(entry.duration_seconds//60)}:{int(entry.duration_seconds%60):02d}]"
                confidence_str = f" ({entry.confidence:.2f})" if entry.confidence else ""
                lines.append(f"{duration_str} {entry.speaker}{confidence_str}: {entry.message}")
            elif entry.message_type == "system":
                lines.append(f"[{entry.timestamp}] ** {entry.message} **")
        
        lines.append("")
        lines.append("=" * 50)
        lines.append("End of Transcript")
        
        return "\n".join(lines)
    
    def get_current_transcript_text(self) -> str:
        """Get current transcript as formatted text"""
        if not self.current_transcript:
            return "No active transcript recording"
        
        return self.generate_text_transcript(self.current_transcript)
    
    def load_transcript(self, filename: str, job_id: str = None, candidate_id: str = None) -> Optional[Transcript]:
        """Load transcript from file with optional job/candidate path"""
        print(f"🔍 Loading transcript: {filename}, job_id={job_id}, candidate_id={candidate_id}")
        
        # Try organized path first, then fall back to root storage
        possible_paths = []
        
        if job_id and candidate_id:
            organized_path = self._get_storage_path(job_id, candidate_id)
            possible_paths.append(os.path.join(organized_path, filename))
            print(f"📁 Trying organized path: {os.path.join(organized_path, filename)}")
        
        if job_id:
            job_path = self._get_storage_path(job_id)
            possible_paths.append(os.path.join(job_path, filename))
            print(f"📁 Trying job path: {os.path.join(job_path, filename)}")
        
        # Always try root storage as fallback
        root_path = os.path.join(self.transcripts_dir, filename)
        possible_paths.append(root_path)
        print(f"📁 Trying root path: {root_path}")
        
        # Also search all directories recursively if not found in organized paths
        if os.path.exists(self.transcripts_dir):
            for root, dirs, files in os.walk(self.transcripts_dir):
                if filename in files:
                    recursive_path = os.path.join(root, filename)
                    possible_paths.append(recursive_path)
                    print(f"📁 Found in recursive search: {recursive_path}")
        
        print(f"🔎 Total paths to check: {len(possible_paths)}")
        
        for filepath in possible_paths:
            print(f"⚡ Checking: {filepath}")
            if os.path.exists(filepath):
                print(f"✅ Found file at: {filepath}")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Reconstruct transcript object
                    entries = [TranscriptEntry(**entry) for entry in data['entries']]
                    data['entries'] = entries
                    
                    transcript = Transcript(**data)
                    print(f"📖 Loaded transcript from {filepath}")
                    return transcript
                    
                except Exception as e:
                    print(f"❌ Error loading transcript from {filepath}: {e}")
                    continue
        
        print(f"❌ Transcript file not found: {filename}")
        return None
    
    def list_transcripts(self, job_id: str = None, candidate_id: str = None) -> List[str]:
        """List transcript files with optional filtering by job_id and/or candidate_id"""
        transcripts = []
        
        if job_id and candidate_id:
            # List transcripts for specific job and candidate
            search_path = self._get_storage_path(job_id, candidate_id)
            if os.path.exists(search_path):
                files = [f for f in os.listdir(search_path) if f.endswith('.json')]
                transcripts.extend(files)
        elif job_id:
            # List all transcripts for a specific job (all candidates)
            job_path = os.path.join(self.transcripts_dir, job_id)
            if os.path.exists(job_path):
                for candidate_dir in os.listdir(job_path):
                    candidate_path = os.path.join(job_path, candidate_dir)
                    if os.path.isdir(candidate_path):
                        files = [f for f in os.listdir(candidate_path) if f.endswith('.json')]
                        transcripts.extend(files)
        elif candidate_id:
            # List all transcripts for a specific candidate across all jobs
            if os.path.exists(self.transcripts_dir):
                for item in os.listdir(self.transcripts_dir):
                    job_path = os.path.join(self.transcripts_dir, item)
                    if os.path.isdir(job_path) and item.startswith('job-'):
                        candidate_path = os.path.join(job_path, candidate_id)
                        if os.path.exists(candidate_path):
                            files = [f for f in os.listdir(candidate_path) if f.endswith('.json')]
                            transcripts.extend(files)
        else:
            # List all transcripts (including organized and root level)
            transcripts = self._get_all_transcripts_recursive()
        
        return sorted(transcripts, reverse=True)  # Most recent first

    def _get_all_transcripts_recursive(self) -> List[str]:
        """Recursively get all transcript files from all directories"""
        all_transcripts = []
        
        if os.path.exists(self.transcripts_dir):
            for root, dirs, files in os.walk(self.transcripts_dir):
                json_files = [f for f in files if f.endswith('.json')]
                all_transcripts.extend(json_files)
        
        return all_transcripts

    def get_transcripts_by_job(self, job_id: str) -> List[str]:
        """Get all transcripts for a specific job"""
        return self.list_transcripts(job_id=job_id)
    
    def get_transcripts_by_candidate(self, candidate_id: str) -> List[str]:
        """Get all transcripts for a specific candidate"""
        return self.list_transcripts(candidate_id=candidate_id)
    
    def get_transcripts_by_job_and_candidate(self, job_id: str, candidate_id: str) -> List[str]:
        """Get all transcripts for a specific job and candidate combination"""
        return self.list_transcripts(job_id=job_id, candidate_id=candidate_id)