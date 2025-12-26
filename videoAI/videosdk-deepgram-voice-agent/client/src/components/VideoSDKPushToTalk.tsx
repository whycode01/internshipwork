import { useMeeting } from '@videosdk.live/react-sdk';
import { Mic, Square } from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';

interface VideoSDKPushToTalkProps {
  silenceTimeout?: number; // Timeout in milliseconds for auto-stop (default 3000ms)
  className?: string;
}

export const VideoSDKPushToTalk: React.FC<VideoSDKPushToTalkProps> = ({
  silenceTimeout = 3000,
  className = '',
}) => {
  const { localParticipant } = useMeeting();
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isPressed, setIsPressed] = useState(false);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopRecordingInternal = useCallback(() => {
    setIsRecording(false);
    setIsPressed(false);
    setAudioLevel(0);
    
    // Clear timers
    if (silenceTimerRef.current) {
      window.clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    // Stop audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    // Disable VideoSDK microphone
    if (localParticipant?.disableMic) {
      localParticipant.disableMic();
    }
    
    console.log('Stopped recording');
  }, [localParticipant]);

  // Voice Activity Detection
  const startVoiceActivityDetection = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      streamRef.current = stream;
      
      const AudioContextConstructor = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioContext = new AudioContextConstructor();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.3;
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      let silentSamples = 0;
      const maxSilentSamples = Math.floor(silenceTimeout / 100); // Check every 100ms
      
      const detectVoice = () => {
        if (!analyser) return;
        
        analyser.getByteFrequencyData(dataArray);
        
        // Calculate average audio level
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        setAudioLevel(average);
        
        // Voice activity detection threshold
        const voiceThreshold = 25; // Adjust this value as needed
        
        if (average > voiceThreshold) {
          // Voice detected, reset silence counter
          silentSamples = 0;
          if (silenceTimerRef.current) {
            window.clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else {
          // Silence detected
          silentSamples++;
          
          if (silentSamples >= maxSilentSamples && !silenceTimerRef.current && !isPressed) {
            // Start silence timer for auto-stop
            silenceTimerRef.current = window.setTimeout(() => {
              stopRecordingInternal();
            }, 500); // Small delay to avoid false positives
          }
        }
        
        if (isRecording) {
          animationFrameRef.current = requestAnimationFrame(detectVoice);
        }
      };
      
      detectVoice();
    } catch (error) {
      console.error('Error setting up voice activity detection:', error);
    }
  }, [silenceTimeout, isPressed, isRecording, stopRecordingInternal]);

  const handleStartRecording = useCallback(async () => {
    try {
      setIsRecording(true);
      
      // Enable VideoSDK microphone
      if (localParticipant?.enableMic) {
        localParticipant.enableMic();
      }
      
      // Start voice activity detection
      await startVoiceActivityDetection();
      
      console.log('Started recording with push-to-talk');
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Unable to access microphone. Please check your permissions.');
      setIsRecording(false);
    }
  }, [localParticipant, startVoiceActivityDetection]);

  const handleStopRecording = useCallback(() => {
    stopRecordingInternal();
  }, [stopRecordingInternal]);

  // Handle mouse/touch events
  const handleMouseDown = () => {
    setIsPressed(true);
    if (!isRecording) {
      handleStartRecording();
    }
  };

  const handleMouseUp = () => {
    setIsPressed(false);
    // Don't stop immediately, let voice activity detection handle auto-stop
  };

  const handleClick = () => {
    if (isRecording) {
      handleStopRecording();
    } else {
      handleStartRecording();
    }
  };

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (isRecording) {
        handleStopRecording();
      }
    };
  }, [handleStopRecording, isRecording]);

  const getButtonStyle = () => {
    const baseClasses = "relative flex items-center justify-center w-24 h-24 rounded-full transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-blue-300/50 shadow-lg";
    
    if (isRecording) {
      return `${baseClasses} bg-red-500 hover:bg-red-600`;
    }
    
    if (isPressed) {
      return `${baseClasses} bg-blue-600 transform scale-95 shadow-inner`;
    }
    
    return `${baseClasses} bg-blue-500 hover:bg-blue-600`;
  };

  const getScaleStyle = () => {
    if (isRecording) {
      const intensity = Math.min(audioLevel / 150, 1);
      const scale = 1 + (intensity * 0.15);
      return { transform: `scale(${scale})` };
    } else if (isPressed) {
      return { transform: 'scale(0.95)' };
    }
    return { transform: 'scale(1)' };
  };

  const getStatusText = () => {
    if (isRecording) {
      if (audioLevel > 25) {
        return "🎤 Speaking...";
      } else {
        return "🔊 Listening...";
      }
    }
    return "Press & Hold to Speak";
  };

  const micStatus = localParticipant?.micOn;

  return (
    <div className={`flex flex-col items-center space-y-4 ${className}`}>
      {/* Main Push-to-Talk Button */}
      <div className="relative">
        <button
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onTouchStart={handleMouseDown}
          onTouchEnd={handleMouseUp}
          onClick={handleClick}
          className={getButtonStyle()}
          style={getScaleStyle()}
        >
          {/* Pulsing ring for recording state */}
          {isRecording && (
            <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping opacity-75" />
          )}
          
          {/* Audio level visualization */}
          {isRecording && audioLevel > 0 && (
            <div 
              className="absolute inset-0 rounded-full bg-gradient-to-r from-red-400 to-red-600 opacity-20 animate-pulse"
              style={{
                transform: `scale(${1 + (audioLevel / 300)})`
              }}
            />
          )}
          
          {/* Icon */}
          {isRecording ? (
            <Square className="w-10 h-10 text-white fill-white" />
          ) : (
            <Mic className="w-10 h-10 text-white" />
          )}
        </button>
        
        {/* VideoSDK Mic Status Indicator */}
        <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-xs font-bold ${
          micStatus ? 'bg-green-500 text-white' : 'bg-gray-500 text-white'
        }`}>
          {micStatus ? '🎤' : '🔇'}
        </div>
      </div>
      
      {/* Status text */}
      <div className="text-center space-y-2">
        <p className={`text-lg font-medium transition-colors ${
          isRecording ? 'text-red-400' : 'text-white'
        }`}>
          {getStatusText()}
        </p>
        
        {isRecording && (
          <p className="text-sm text-gray-400">
            Auto-stops after {silenceTimeout / 1000}s of silence
          </p>
        )}
      </div>
      
      {/* Audio level meter */}
      {isRecording && (
        <div className="w-40 space-y-2">
          <div className="flex justify-between text-xs text-gray-400">
            <span>Quiet</span>
            <span>Audio Level</span>
            <span>Loud</span>
          </div>
          <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-150 rounded-full ${
                audioLevel > 60 ? 'bg-gradient-to-r from-yellow-400 to-red-500' :
                audioLevel > 30 ? 'bg-gradient-to-r from-green-400 to-yellow-400' :
                'bg-gradient-to-r from-blue-400 to-green-400'
              }`}
              style={{ width: `${Math.min((audioLevel / 128) * 100, 100)}%` }}
            />
          </div>
        </div>
      )}
      
      {/* Instructions */}
      <div className="text-center max-w-sm">
        <p className="text-sm text-gray-400 leading-relaxed">
          <strong>Hold</strong> to speak continuously, or <strong>click</strong> to toggle. 
          Automatically stops after {silenceTimeout / 1000} seconds of silence.
        </p>
      </div>
    </div>
  );
};