import { useRef, useState } from "react";

function AudioRecorder({ userId, onTranscript, onLlmReply }) {
  const [isRecording, setIsRecording] = useState(false);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const silenceTimerRef = useRef(null);

  const detectSilence = (stream, onSilence, thresholdMs = 5000) => {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = ctx.createAnalyser();
    const mic = ctx.createMediaStreamSource(stream);
    mic.connect(analyser);
    analyser.fftSize = 2048;
    const data = new Uint8Array(analyser.fftSize);
    let lastSoundTime = performance.now();

    const loop = () => {
      analyser.getByteTimeDomainData(data);
      const isSilent = data.every(val => Math.abs(val - 128) < 6);
      if (!isSilent) lastSoundTime = performance.now();

      if (performance.now() - lastSoundTime > thresholdMs) {
        onSilence();
        ctx.close();
      } else {
        silenceTimerRef.current = requestAnimationFrame(loop);
      }
    };

    loop();
  };

  const startRecording = async () => {
    setIsRecording(true);
    if (onTranscript) onTranscript("");

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ws = new WebSocket(`ws://localhost:8000/ws/audio?user_id=${encodeURIComponent(userId)}`);
    wsRef.current = ws;

    let finalText = "";

    ws.onmessage = event => {
      finalText = event.data;
      if (onTranscript) onTranscript(event.data);
    };

    ws.onopen = () => {
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = e => {
        if (ws.readyState === WebSocket.OPEN && e.data.size > 0) {
          ws.send(e.data);
        }
      };

      recorder.start(250);
      detectSilence(stream, stopRecording, 5000);
    };

    ws.onclose = () => {
      setIsRecording(false);
      stream.getTracks().forEach(t => t.stop());
      cancelAnimationFrame(silenceTimerRef.current);
      if (onLlmReply && finalText.trim()) {
        onLlmReply(finalText.trim());
      }
    };

    ws.onerror = err => {
      console.error("WS Error", err);
      setIsRecording(false);
      stream.getTracks().forEach(t => t.stop());
      cancelAnimationFrame(silenceTimerRef.current);
    };
  };

  const stopRecording = () => {
    setIsRecording(false);
    mediaRecorderRef.current?.stop();
    wsRef.current?.close();
    cancelAnimationFrame(silenceTimerRef.current);
  };

  return (
    <div>
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>
    </div>
  );
}

export default AudioRecorder;
