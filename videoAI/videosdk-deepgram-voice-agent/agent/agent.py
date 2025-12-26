import asyncio
import os
import sys

# Add the parent directory to the path to import transcript manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# types
from videosdk import (Meeting, MeetingConfig, MeetingEventHandler, Participant,
                      ParticipantEventHandler, PubSubPublishConfig, Stream,
                      VideoSDK)
from videosdk.stream import MediaStreamTrack

from intelligence.intelligence import Intelligence
from stt.stt import STT
from transcript.transcript_manager import TranscriptManager


class AIInterviewer:
    def __init__(self, loop:asyncio.AbstractEventLoop, audio_track: MediaStreamTrack, stt: STT, intelligence: Intelligence, agent_name: str = "AI Agent", job_id: str = None, candidate_id: str = None):
        self.name = agent_name
        self.loop = loop
        self.meeting: Meeting = None
        self.stt: STT = stt
        self.intelligence: Intelligence = intelligence
        self.audio_track = audio_track
        self.has_introduced = False  # Track if agent has introduced itself
        self.job_id = job_id
        self.candidate_id = candidate_id
        
        # Initialize transcript manager
        self.transcript_manager = TranscriptManager()
        self.current_interview_id = None

    async def join(self, meeting_id: str, token: str):
        print(meeting_id, token)
        
        # Start transcript recording with job and candidate info
        self.current_interview_id = self.transcript_manager.start_recording(
            meeting_id=meeting_id,
            job_id=self.job_id,
            candidate_id=self.candidate_id,
            participants=[self.name],
            metadata={"agent_name": self.name, "job_id": self.job_id, "candidate_id": self.candidate_id}
        )
        
        meeting_config = MeetingConfig(
            meeting_id=meeting_id,
            name=self.name,
            mic_enabled=True,
            webcam_enabled=False,
            custom_microphone_audio_track=self.audio_track,
            token=token,
        )
        self.meeting = VideoSDK.init_meeting(**meeting_config)

        self.meeting.add_event_listener(MyMeetingEventListener(stt=self.stt, agent=self))

        await self.meeting.async_join()

        self.stt.set_pubsub(pubsub=self.publish_message)
        self.intelligence.set_pubsub(pubsub=self.publish_message)
        
        # Set transcript manager for STT and Intelligence
        self.stt.set_transcript_manager(self.transcript_manager)
        self.intelligence.set_transcript_manager(self.transcript_manager)

    def publish_message(self, message):
        self.loop.create_task(self.meeting.pubsub.publish(
            PubSubPublishConfig(
                topic="CHAT",
                message=message,
            )
        ))
    
    def introduce_agent(self):
        """Make the AI agent introduce itself"""
        if not self.has_introduced:
            self.has_introduced = True
            print("🤖 AI Agent introducing itself...")
            
            # Get the first question from the intelligence client dynamically
            first_question = self._get_first_question()
            
            # Create introduction message with dynamic question
            if first_question:
                introduction = f"Hello! I'm {self.name}. Let's begin with our first question: {first_question}"
            else:
                introduction = f"Hello! I'm {self.name}. Let's begin our interview. Please tell me about yourself and your background."
            
            # Send introduction to intelligence for TTS processing
            self.intelligence.generate(text=introduction, sender_name=self.name, is_agent_introduction=True)
            
            # Record introduction in transcript
            if hasattr(self, 'transcript_manager') and self.transcript_manager:
                self.transcript_manager.add_entry(self.name, introduction, message_type="speech")
    
    def _get_first_question(self):
        """Get the first appropriate question based on loaded questions"""
        try:
            # Try to get a question from the intelligence client's question manager
            if hasattr(self.intelligence, 'questions_manager') and self.intelligence.questions_manager:
                # For API-based managers
                if hasattr(self.intelligence.questions_manager, 'questions_data'):
                    questions_data = self.intelligence.questions_manager.questions_data
                    if questions_data and 'questions' in questions_data:
                        questions = questions_data['questions']
                        if questions:
                            # Get the first question
                            first_q = questions[0]
                            return first_q.get('text', first_q.get('question', ''))
                
                # For file-based managers
                elif hasattr(self.intelligence.questions_manager, 'get_current_questions'):
                    questions = self.intelligence.questions_manager.get_current_questions()
                    if questions:
                        return questions[0].text
            
            # Fallback to None if no questions available
            return None
            
        except Exception as e:
            print(f"⚠️ Error getting first question: {e}")
            return None

    async def leave(self):
        print("leaving meeting...")
        
        # End transcript recording
        if self.transcript_manager and self.current_interview_id:
            filename = self.transcript_manager.end_recording()
            print(f"📝 Interview transcript saved: {filename}")
        
        self.meeting.leave()


class MyMeetingEventListener(MeetingEventHandler):
    def __init__(self, stt: STT, agent):
        super().__init__()
        self.stt = stt
        self.agent = agent
        print("Meeting :: EventListener initialized")

    def on_meeting_state_change(self, data):
        print("Meeting state changed", data)

    def on_meeting_joined(self, data):
        print("Meeting joined")
        # Introduce the agent after a short delay to ensure everything is set up
        asyncio.create_task(self._delayed_introduction())
    
    async def _delayed_introduction(self):
        """Introduce the agent after a brief delay"""
        await asyncio.sleep(2)  # Wait 2 seconds for everything to be ready
        self.agent.introduce_agent()

    def on_meeting_left(self, data):
        print("Meeting left")

    def on_participant_joined(self, participant: Participant):
        print(f"Participant {participant.display_name} joined")
        
        # Add participant to transcript
        if hasattr(self.agent, 'transcript_manager') and self.agent.transcript_manager:
            self.agent.transcript_manager.add_participant(participant.display_name)
        
        participant.add_event_listener(
            MyParticipantEventListener(stt=self.stt, participant=participant)
        )

    def on_participant_left(self, participant: Participant):
        print(f"Participant {participant.display_name} left")
        self.stt.stop(peer_id=participant.id)


class MyParticipantEventListener(ParticipantEventHandler):
    def __init__(self, stt: STT, participant: Participant):
        super().__init__()
        self.stt = stt
        self.participant = participant
        self.dummy_tracks: dict[str, asyncio.Task] = {}
        print(f"Participant-{participant.display_name} :: EventListener initialized")

    async def dummy(self, track):
        try:
            while True:
                await track.recv()
        except Exception as e:
            print("error while consuming dummy stream", e)

    def on_stream_enabled(self, stream: Stream):
        print(
            f"Participant-{self.participant.display_name} :: {stream.kind} stream enabled"
        )
        if stream.kind == "audio":
            self.stt.start(
                peer_id=self.participant.id,
                peer_name=self.participant.display_name,
                stream=stream,
            )
        else:
            # create dummy stream to consume video/screenshare stream to reduce memory usage
            self.dummy_tracks[stream.track.id] = asyncio.create_task(
                self.dummy(track=stream.track)
            )

    def on_stream_disabled(self, stream: Stream):
        print(
            f"Participant-{self.participant.display_name} :: {stream.kind} stream disabled"
        )
        if stream.kind == "audio":
            self.stt.stop(peer_id=self.participant.id)
        else:
            if stream.track.id in self.dummy_tracks:
                self.dummy_tracks[stream.track.id].cancel()
                del self.dummy_tracks[stream.track.id]


