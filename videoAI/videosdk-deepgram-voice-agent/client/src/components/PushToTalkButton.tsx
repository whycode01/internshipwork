import { Mic, Square } from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';

interface PushToTalkButtonProps {
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  silenceTimeout?: number; // Timeout in milliseconds for auto-stop (default 3000ms)
  className?: string;
}

export const PushToTalkButton: React.FC<PushToTalkButtonProps> = ({
  onStartRecording,
  onStopRecording,
  silenceTimeout = 3000,
  className = '',
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isPressed, setIsPressed] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Voice Activity Detection
  const startVoiceActivityDetection = useCallback((stream: MediaStream) => {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
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
        const voiceThreshold = 30; // Adjust this value as needed
        
        if (average > voiceThreshold) {
          // Voice detected, reset silence counter
          silentSamples = 0;
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else {
          // Silence detected
          silentSamples++;
          
          if (silentSamples >= maxSilentSamples && !silenceTimerRef.current) {
            // Start silence timer for auto-stop
            silenceTimerRef.current = setTimeout(() => {
              if (isRecording && !isPressed) {
                handleStopRecording();
              }
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
  }, [isRecording, isPressed, silenceTimeout]);

  const handleStartRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      streamRef.current = stream;
      setIsRecording(true);
      
      // Start voice activity detection
      startVoiceActivityDetection(stream);
      
      // Optional: Start MediaRecorder for actual recording
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      onStartRecording?.();
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Unable to access microphone. Please check your permissions.');
    }
  }, [onStartRecording, startVoiceActivityDetection]);

  const handleStopRecording = useCallback(() => {
    setIsRecording(false);
    setIsPressed(false);
    setAudioLevel(0);
    
    // Clear timers
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
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
    
    onStopRecording?.();
  }, [onStopRecording]);

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
  }, []);

  // Calculate visual feedback based on audio level and recording state
  const getButtonStyle = () => {
    const baseClasses = "relative flex items-center justify-center w-20 h-20 rounded-full transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-blue-300/50";
    
    if (isRecording) {
      return `${baseClasses} bg-red-500 hover:bg-red-600 shadow-lg`;
    }
    
    if (isPressed) {
      return `${baseClasses} bg-blue-600 transform scale-95 shadow-inner`;
    }
    
    return `${baseClasses} bg-blue-500 hover:bg-blue-600 shadow-md`;
  };

  const getScaleStyle = () => {
    if (isRecording) {
      const intensity = Math.min(audioLevel / 100, 1);
      const scale = 1 + (intensity * 0.2);
      return { transform: `scale(${scale})` };
    } else if (isPressed) {
      return { transform: 'scale(0.95)' };
    }
    return { transform: 'scale(1)' };
  };

  const getStatusText = () => {
    if (isRecording) {
      if (audioLevel > 30) {
        return "Speaking...";
      } else {
        return "Listening...";
      }
    }
    return "Press & Hold to Talk";
  };

  return (
    <div className={`flex flex-col items-center space-y-3 ${className}`}>
      <button
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleMouseDown}
        onTouchEnd={handleMouseUp}
        onClick={handleClick}
        className={getButtonStyle()}
        disabled={false}
        style={getScaleStyle()}
      >
        {/* Pulsing ring for recording state */}
        {isRecording && (
          <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping" />
        )}
        
        {/* Audio level visualization */}
        {isRecording && audioLevel > 0 && (
          <div 
            className="absolute inset-0 rounded-full bg-gradient-to-r from-red-400 to-red-600 opacity-30"
            style={{
              transform: `scale(${1 + (audioLevel / 200)})`
            }}
          />
        )}
        
        {/* Icon */}
        {isRecording ? (
          <Square className="w-8 h-8 text-white fill-white" />
        ) : (
          <Mic className="w-8 h-8 text-white" />
        )}
      </button>
      
      {/* Status text */}
      <div className="text-center">
        <p className={`text-sm font-medium transition-colors ${
          isRecording ? 'text-red-400' : 'text-gray-400'
        }`}>
          {getStatusText()}
        </p>
        
        {isRecording && (
          <p className="text-xs text-gray-500 mt-1">
            Auto-stops after {silenceTimeout / 1000}s of silence
          </p>
        )}
      </div>
      
      {/* Audio level meter */}
      {isRecording && (
        <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-green-400 to-red-500 transition-all duration-100 rounded-full"
            style={{ width: `${Math.min((audioLevel / 128) * 100, 100)}%` }}
          />
        </div>
      )}
      
      {/* Instructions */}
      <div className="text-center max-w-xs">
        <p className="text-xs text-gray-500">
          Hold the button to talk, release to pause, or click to toggle. 
          Recording stops automatically after {silenceTimeout / 1000} seconds of silence.
        </p>
      </div>
    </div>
  );
};