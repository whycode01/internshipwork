from abc import ABC, abstractmethod

from videosdk import Stream


class Intelligence(ABC):
    def __init__(self):
        """Initialize the Intelligence interface."""
        self.transcript_manager = None
    
    def set_transcript_manager(self, transcript_manager):
        """Set the transcript manager for recording conversations"""
        self.transcript_manager = transcript_manager

    @abstractmethod
    def generate(self, text: str, sender_name: str, is_agent_introduction: bool = False):
        """generate new message based on text."""
        pass
