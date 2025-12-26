from abc import ABC, abstractmethod

from videosdk import Stream


class STT(ABC):
    def __init__(self):
        """Initialize the STT interface."""
        self.transcript_manager = None
    
    def set_transcript_manager(self, transcript_manager):
        """Set the transcript manager for recording conversations"""
        self.transcript_manager = transcript_manager

    @abstractmethod
    def start(self, peer_id, peer_name, stream: Stream):
        """Start the speech-to-text listening process."""
        pass

    @abstractmethod
    def stop(self, peer_id):
        """Stop the speech-to-text listening process."""
        pass

