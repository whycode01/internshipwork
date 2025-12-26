import { useEffect, useRef } from "react";
function WaveformVisualizer({ stream, isActive }) {
  const canvasRef = useRef();

  useEffect(() => {
    if (!isActive || !stream) return;
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    source.connect(analyser);
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    function draw() {
      if (!isActive) return;
      analyser.getByteTimeDomainData(dataArray);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.beginPath();
      for (let i = 0; i < bufferLength; i++) {
        const x = (i / bufferLength) * canvas.width;
        const y = canvas.height / 2 + ((dataArray[i] - 128) / 128) * (canvas.height / 2.4);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "#4460ef";
      ctx.lineWidth = 2;
      ctx.stroke();
      if (isActive) requestAnimationFrame(draw);
    }
    draw();
    return () => {
      audioCtx.close();
    };
  }, [isActive, stream]);
  return <canvas ref={canvasRef} width={340} height={60} className="waveform-canvas" />;
}
export default WaveformVisualizer;
