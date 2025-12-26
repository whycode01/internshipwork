import { useEffect, useRef, useState } from "react";
import "./App.css";
import AudioRecorder from "./components/AudioRecorder";
import TranscriptDisplay from "./components/TranscriptDisplay";

function App() {
  const [userId, setUserId] = useState("anonymous");
  const initialized = useRef(false);
  const [transcript, setTranscript] = useState("");
  const [llmReply, setLlmReply] = useState("");
  const [messages, setMessages] = useState([]); // 🧠 Conversation history
  const spokenRef = useRef("");

  useEffect(() => {
    if (!initialized.current) {
      const username = prompt("Enter your user ID:", "anonymous");
      setUserId(username?.trim() || "anonymous");
      initialized.current = true;
    }
  }, []);

  useEffect(() => {
    if (
      llmReply &&
      llmReply !== spokenRef.current &&
      "speechSynthesis" in window
    ) {
      const utter = new SpeechSynthesisUtterance(llmReply);
      utter.lang = "en-US";
      utter.rate = 1;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
      spokenRef.current = llmReply;
    }
  }, [llmReply]);

  const handleTranscriptComplete = async (text) => {
    const updatedMessages = [...messages, { role: "user", content: text }];
    setMessages(updatedMessages);

    try {
      const res = await fetch("http://localhost:8000/api/llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, messages: updatedMessages }),
      });
      const data = await res.json();
      if (data.reply) {
        const newMessages = [...updatedMessages, { role: "assistant", content: data.reply }];
        setMessages(newMessages);
        setLlmReply(data.reply);
      }
    } catch (error) {
      console.error("LLM error:", error);
      setLlmReply("⚠️ Failed to fetch reply from AI.");
    }
  };

  return (
    <div className="App">
      <header className="topbar">
        <div className="logo">🎙️ Interview AI</div>
      </header>
      <main className="main-container">
        <h1>Real-time Interview Assistant</h1>
        <p className="subtitle">
          Speak your answers. Let the AI reply and continue the conversation 🧠
        </p>

        <AudioRecorder
          userId={userId}
          onTranscript={setTranscript}
          onLlmReply={handleTranscriptComplete}
        />

        <TranscriptDisplay transcript={transcript || "Waiting for your voice..."} />

        <div className="output-section">
          <div className="output-label">Conversation History</div>
          <div className="output-box" style={{ minHeight: 160, textAlign: "left" }}>
            {messages.length === 0
              ? <em>Your conversation will appear here...</em>
              : messages.map((m, i) => (
                  <p key={i}>
                    <strong>{m.role === "user" ? "🧑 You" : "🤖 AI"}:</strong> {m.content}
                  </p>
                ))}
          </div>

  {llmReply && (
  <div style={{ display: "flex", justifyContent: "center", marginTop: "1.2rem" }}>
    <div style={{ display: "flex", gap: "1.3rem" }}>
      <button
        onClick={() => {
          window.speechSynthesis.cancel();
          const synth = new SpeechSynthesisUtterance(llmReply);
          synth.lang = "en-US";
          window.speechSynthesis.speak(synth);
        }}
      >
        🔊 Listen Again
      </button>
      <button
        onClick={() => {
          window.speechSynthesis.cancel();
        }}
        style={{ background: "#ef5350", color: "#fff" }}
      >
        ⏹️ Stop AI Voice
      </button>
    </div>
  </div>
)}


        </div>
      </main>
    </div>
  );
}

export default App;
