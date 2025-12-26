import "../App.css";

function TranscriptDisplay({ transcript, keywords = [] }) {
  return (
    <div className="output-section">
      <div className="output-label">Live Transcript</div>
      <div className="output-box" tabIndex={0} aria-live="polite">
        {transcript}
      </div>
    </div>
  );
}

export default TranscriptDisplay;
