import asyncio
import time
import traceback
from asyncio import AbstractEventLoop, Task
from asyncio.log import logger
from datetime import datetime, timezone
from typing import Dict, List

import numpy as np
from deepgram import (DeepgramClient, DeepgramClientOptions, LiveOptions,
                      LiveTranscriptionEvents)
from videosdk import Stream
from vsaiortc.mediastreams import MediaStreamError

from intelligence.intelligence import Intelligence
from stt.stt import STT

LEARNING_RATE = 0.1
LENGTH_THRESHOLD = 5
SMOOTHING_FACTOR = 3
BASE_WPM = 150.0
VAD_THRESHOLD_MS = 50   # Voice activity detection threshold
UTTERANCE_CUTOFF_MS = 800   # Shorter cutoff for faster response
SILENCE_THRESHOLD_MS = 1000  # Only 1 second of silence before responding

class DeepgramSTT(STT):

    def __init__(
        self,
        loop: AbstractEventLoop,
        api_key,
        language,
        intelligence:Intelligence
    ) -> None:
        super().__init__()  # Initialize base STT class
        self.loop = loop

        self.vad_threshold_ms: int = VAD_THRESHOLD_MS
        self.utterance_cutoff_ms: int = UTTERANCE_CUTOFF_MS
        self.silence_threshold_ms: int = SILENCE_THRESHOLD_MS
        self.model = "nova-2"
        self.speed_coefficient: float = 1.0
        self.wpm_0 = BASE_WPM * self.speed_coefficient
        self.wpm = self.wpm_0
        self.speed_coefficient = self.speed_coefficient

        self.buffer = ""
        self.words_buffer = []
        self.last_speech_time = None  # Track when user last spoke
        self.is_speaking = False  # Track if user is currently speaking
        self.accumulated_transcript = ""  # Accumulate transcript for longer sentences

        # Validate API key before creating client
        if not api_key or len(api_key) < 10:
            print(f"❌ Invalid Deepgram API key: {api_key[:10] if api_key else 'None'}...")
            raise ValueError("Invalid Deepgram API key")
        
        print(f"🔧 Initializing Deepgram client with API key: {api_key[:10]}...")
        
        try:
            self.deepgram_client = DeepgramClient(
                api_key=api_key,
                config=DeepgramClientOptions(options={"keepalive": True}),
            )
            print("✅ Deepgram client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Deepgram client: {e}")
            raise
        self.language = language
        self.deepgram_connections = {}  # Use generic dict since we're updating API
        self.audio_tasks:Dict[str, Task] = {}

        self.finalize_called: Dict[str, bool] = {}

        # intelligence
        self.intelligence = intelligence
        self.pubsub = None
    
    def set_pubsub(self, pubsub):
        self.pubsub = pubsub

    def start(self, peer_id: str, peer_name: str, stream:Stream):

        def on_deepgram_stt_text_available(connection, result, **kwargs):
            self.on_deepgram_stt_text_available(peer_id=peer_id, peer_name=peer_name, result=result)

        def on_utterance_end(connection, utterance_end, **kwargs):
            self.on_utterance_end(peer_id=peer_id, peer_name=peer_name)
        
        def on_open(connection, open, **kwargs):
            self.on_open(peer_id=peer_id, peer_name=peer_name)

        def on_metadata(connection, metadata, **kwargs):
            self.on_metadata(peer_id=peer_id, peer_name=peer_name, metadata=metadata)

        def on_speech_started(connection, speech_started, **kwargs):
            self.on_speech_started(peer_id=peer_id, peer_name=peer_name)
            
        def on_close(connection, close, **kwargs):
            self.on_close(peer_id=peer_id, peer_name=peer_name)

        def on_error(connection, error, **kwargs):
            self.on_error(peer_id=peer_id, peer_name=peer_name, error=error)

        def on_unhandled(connection, unhandled, **kwargs):
            self.on_unhandled(peer_id=peer_id, peer_name=peer_name, unhandled=unhandled)

        # Simplified and validated deepgram options to avoid HTTP 400 error
        deepgram_options = LiveOptions(
            model=self.model,
            language=self.language,
            smart_format=True,
            encoding="linear16",
            channels=2,
            sample_rate=48000,
            interim_results=True,
            punctuate=True,
            # Removed problematic options that might cause HTTP 400
            # endpointing=int(self.vad_threshold_ms * (1 / self.speed_coefficient)),
            # utterance_end_ms=max(
            #     int(self.utterance_cutoff_ms * (1 / self.speed_coefficient)), 800
            # ),
        )
        # Create websocket connection using the new API
        deepgram_connection = self.deepgram_client.listen.websocket.v("1")

        deepgram_connection.on(
            LiveTranscriptionEvents.Transcript, on_deepgram_stt_text_available
        )
        deepgram_connection.on(LiveTranscriptionEvents.Open, on_open)
        deepgram_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        deepgram_connection.on(
            LiveTranscriptionEvents.SpeechStarted, on_speech_started
        )
        deepgram_connection.on(
            LiveTranscriptionEvents.UtteranceEnd, on_utterance_end
        )
        deepgram_connection.on(LiveTranscriptionEvents.Close, on_close)
        deepgram_connection.on(LiveTranscriptionEvents.Error, on_error)
        deepgram_connection.on(
            LiveTranscriptionEvents.Unhandled, on_unhandled
        )
        
        # Start connection with comprehensive error handling
        try:
            print(f"🔧 Starting Deepgram connection with options:")
            print(f"   Model: {self.model}")
            print(f"   Language: {self.language}")
            print(f"   Sample Rate: 48000")
            print(f"   Channels: 2")
            
            result = deepgram_connection.start(deepgram_options)
            print(f"🔧 Connection start result: {result}")
            
            if result is False:
                print("❌ Failed to start Deepgram connection - result is False")
                return
            
            print("✅ Deepgram WebSocket connection started successfully")
            
        except Exception as e:
            print(f"❌ Error starting Deepgram connection: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            if "400" in str(e):
                print("❌ HTTP 400 error - likely invalid parameters or API key issue")
                print("🔧 Trying with minimal options...")
                
                # Try with minimal options
                minimal_options = LiveOptions(
                    model="nova-2",
                    language="en-US",
                    encoding="linear16",
                    sample_rate=48000,
                    interim_results=True
                )
                
                try:
                    result = deepgram_connection.start(minimal_options)
                    if result:
                        print("✅ Minimal options connection succeeded")
                    else:
                        print("❌ Even minimal options failed")
                        return
                except Exception as minimal_error:
                    print(f"❌ Minimal options also failed: {minimal_error}")
                    return
            else:
                return

        self.deepgram_connections[peer_id] = deepgram_connection

        self.finalize_called[peer_id] = False
        self.task = self.loop.create_task(
            self.add_peer_stream(
                stream=stream, peer_id=peer_id, peer_name=peer_name
            )
        )

    def stop(self, peer_id):
        if peer_id in self.deepgram_connections:
            print("stop peer audio connection", peer_id)
            self.deepgram_connections[peer_id].finalize()
            self.deepgram_connections[peer_id].finish()
            self.finalize_called[peer_id] = True    
            del self.deepgram_connections[peer_id]

    def get_usage(self):
        current_usage = self.usage
        self.usage = 0
        return current_usage

    async def add_peer_stream(self, stream: Stream, peer_id: str, peer_name: str):
        try:
            track = stream.track

            while not self.finalize_called[peer_id]:
                frame = await track.recv()
                audio_data = frame.to_ndarray()
                pcm_frame = audio_data.flatten().astype(np.int16).tobytes()
                
                # Check if connection is still valid before sending
                if peer_id in self.deepgram_connections:
                    connection = self.deepgram_connections[peer_id]
                    if hasattr(connection, '_socket') and connection._socket is not None:
                        connection.send(pcm_frame)
                    elif hasattr(connection, 'send'):
                        # Try to send anyway, let Deepgram handle the error
                        try:
                            connection.send(pcm_frame)
                        except Exception as send_error:
                            print(f"⚠️ Error sending audio frame: {send_error}")
                            # Don't break the loop, just log the error
                    else:
                        print(f"⚠️ WebSocket connection not ready for peer {peer_id}")
                        # Small delay before retrying
                        await asyncio.sleep(0.1)
                else:
                    print(f"⚠️ No connection found for peer {peer_id}")
                    break
                    
        except Exception as e:
            traceback.print_exc()
            print("Error while sending audio to STT Server", e)

    def on_deepgram_stt_text_available(self, peer_id, peer_name, result):
        try:
            top_choice = result.channel.alternatives[0]

            if len(top_choice.transcript) == 0:
                return

            current_time = time.time()
            
            # Update speaking status
            if top_choice.transcript and top_choice.confidence > 0.0:
                self.is_speaking = True
                self.last_speech_time = current_time
                
                # Handle interim results (real-time transcription)
                if not result.is_final:
                    # Show interim transcript but don't process yet
                    interim_text = f"{self.accumulated_transcript} {top_choice.transcript}".strip()
                    print(f"[Interim] {peer_name}: {interim_text}")
                    return
                
                # Handle final results
                if result.is_final:
                    # Add to accumulated transcript
                    if self.accumulated_transcript:
                        self.accumulated_transcript += f" {top_choice.transcript}"
                    else:
                        self.accumulated_transcript = top_choice.transcript
                    
                    # Get words for duration calculation
                    words = top_choice.words
                    if words:
                        self.words_buffer.extend(words)
                    
                    print(f"[Accumulated] {peer_name}: {self.accumulated_transcript}")
                    
                    # Check if transcript has ending punctuation (complete sentence)
                    clean_text = self.accumulated_transcript.strip()
                    if clean_text.endswith(('.', '!', '?')):
                        print("⚡ Complete sentence detected - IMMEDIATE processing (ZERO wait)")
                        self.finalize_accumulated_transcript(peer_name)
                        return
                    
                    # Check for very short responses that should be processed immediately
                    clean_text_lower = clean_text.lower()
                    quick_responses = ['yes', 'no', 'okay', 'ok', 'sure', 'maybe', 'hello', 'hi', 'thanks', 'thank you', 'exactly', 'correct']
                    if any(clean_text_lower == response or clean_text_lower.endswith(f' {response}') for response in quick_responses):
                        print("⚡ Quick response detected - immediate processing")
                        self.finalize_accumulated_transcript(peer_name)
                        return
                    
                    # For responses longer than 5 words, finalize immediately
                    transcript_words = self.accumulated_transcript.strip().split()
                    if len(transcript_words) > 5:
                        print(f"⚡ Long response detected ({len(transcript_words)} words) - IMMEDIATE processing")
                        self.finalize_accumulated_transcript(peer_name)
                        return

            # Check for delayed finalization due to silence OR force finalization
            if self.accumulated_transcript and self.should_finalize_transcript(current_time):
                self.finalize_accumulated_transcript(peer_name)
            
            # FORCE finalization if we have accumulated text waiting more than 2 seconds
            elif (self.accumulated_transcript and self.last_speech_time and 
                  current_time - self.last_speech_time > 2.0):
                print(f"🚨 FORCE finalization - transcript waiting {current_time - self.last_speech_time:.1f}s")
                self.finalize_accumulated_transcript(peer_name)

        except Exception as e:
            print("Error while transcript processing", e)
            traceback.print_exc()

    def should_finalize_transcript(self, current_time):
        """Determine if we should finalize the accumulated transcript"""
        
        # Finalize if enough silence has passed since last speech
        if (self.last_speech_time and 
            current_time - self.last_speech_time > (self.silence_threshold_ms / 1000.0)):
            elapsed_silence = current_time - self.last_speech_time
            print(f"📝 Finalizing: {elapsed_silence:.1f}s silence threshold reached")
            return True
            
        return False

    def finalize_accumulated_transcript(self, peer_name):
        """Finalize and process the accumulated transcript"""
        print(f"🎯 [FINALIZE] Called for peer: {peer_name}")
        
        if not self.accumulated_transcript.strip():
            print(f"⚠️ [FINALIZE] No accumulated transcript to process")
            return
            
        try:
            print(f"⚡ [FINALIZE] Starting transcript processing...")
            start_time = time.time()
            
            # Skip WPM calculation for speed - just process immediately
            final_text = self.accumulated_transcript.strip()
            print(f"✅ [FINALIZE] Final text: '{final_text}'")
            
            # Send to intelligence for processing IMMEDIATELY
            print(f"📤 [FINALIZE] Calling produce_text...")
            self.produce_text(final_text, peer_name=peer_name, is_final=True, confidence=None)
            print(f"✅ [FINALIZE] produce_text completed")
            
            # Reset for next utterance
            print(f"🔄 [FINALIZE] Resetting transcript state...")
            self.reset_transcript_state()
            print(f"✅ [FINALIZE] Reset completed")
            
            elapsed = time.time() - start_time
            print(f"⏱️ [FINALIZE] TOTAL finalization time: {elapsed:.3f} seconds")
            
        except Exception as e:
            print(f"❌ [FINALIZE] Error: {e}")
            import traceback
            traceback.print_exc()

    def reset_transcript_state(self):
        """Reset state for next utterance"""
        self.accumulated_transcript = ""
        self.buffer = ""
        self.words_buffer = []
        self.is_speaking = False
        self.last_speech_time = None

    def on_open(self, peer_id, peer_name):
        print(f"✅ Deepgram connection opened for {peer_name}")

    def on_metadata(self, peer_id, peer_name, metadata):
        print(f"📊 Deepgram metadata: {metadata}")

    def on_speech_started(self, peer_id, peer_name):
        print(f"🎤 [{peer_name}] Speech Started")
        self.is_speaking = True
        self.last_speech_time = time.time()

    def on_utterance_end(self, peer_id, peer_name):
        print(f"🔚 Utterance End detected")
        # Force finalize if we have accumulated transcript
        if self.accumulated_transcript.strip():
            print("🔚 Force finalizing due to utterance end")
            self.finalize_accumulated_transcript(peer_name)

    def on_close(self, peer_id, peer_name):
        print(f"🔌 Deepgram connection closed for {peer_name}")

    def on_error(self, peer_id, peer_name, error):
        print(f"❌ Deepgram Error for {peer_name}: {error}")
        # Try to restart connection if needed
        if "WebSocket" in str(error) or "connection" in str(error).lower():
            print(f"🔄 WebSocket error detected, connection may need restart")

    def on_unhandled(self, peer_id, peer_name, unhandled):
        print(f"⚠️ Unhandled Deepgram message for {peer_name}: {unhandled}")

    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def is_endpoint(self, deepgram_response):
        is_endpoint = (deepgram_response.channel.alternatives[0].transcript) and (
            deepgram_response.speech_final
        )
        return is_endpoint

    def calculate_duration(self, words: List[dict]) -> float:
        if len(words) == 0:
            return 0.0
        return words[-1]["end"] - words[0]["start"]

    def produce_text(self, text: str, peer_name: str, is_final: bool = False, confidence: float = None):
        try:
            print(f"🔄 [PRODUCE_TEXT] Called with: text='{text[:50]}...', is_final={is_final}")
            
            if is_final and text and text.strip():
                # Peer final message after speech
                clean_text = text.strip()
                print(f"🎯 [PROCESSING] {peer_name}: {clean_text}")
                
                print(f"📢 [PUBSUB] Publishing to meeting chat...")
                if self.pubsub is not None:
                    # Publish in meeting
                    self.pubsub(message=f"[{peer_name}]: {clean_text}")
                    print(f"✅ [PUBSUB] Published successfully")
                else:
                    print(f"⚠️ [PUBSUB] No pubsub available")
                
                # Send to AI for processing
                print(f"🧠 [INTELLIGENCE] Sending to AI for processing...")
                intelligence_start = time.time()
                
                # Record user speech in transcript
                if self.transcript_manager:
                    self.transcript_manager.add_entry(peer_name, clean_text, confidence=confidence, message_type="speech")
                
                self.intelligence.generate(text=clean_text, sender_name=peer_name)
                
                intelligence_elapsed = time.time() - intelligence_start
                print(f"✅ [INTELLIGENCE] Completed in {intelligence_elapsed:.3f} seconds")
                
            elif text and not is_final:
                # Interim text - just for display
                print(f"🔄 [INTERIM] {peer_name}: {text}")
                
        except Exception as e:
            print(f"❌ [PRODUCE_TEXT] Error: {e}")
            import traceback
            traceback.print_exc()

    def update_speed_coefficient(self, wpm: int, message: str):
        if wpm is not None:
            length = len(message.strip().split())
            p_t = min(
                1,
                LEARNING_RATE
                * ((length + SMOOTHING_FACTOR) / (LENGTH_THRESHOLD + SMOOTHING_FACTOR)),
            )
            self.wpm = self.wpm * (1 - p_t) + wpm * p_t
            self.speed_coefficient = self.wpm / BASE_WPM
            logger.info(f"Set speed coefficient to {self.speed_coefficient}")