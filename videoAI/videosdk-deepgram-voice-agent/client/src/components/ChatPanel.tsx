import { Check, Clipboard, Download, MessageSquare } from "lucide-react";
import React, { useState } from "react";
import { ChatPanelProps, Message } from "../types/meeting";

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isAIConnected,
  meetingId,
}) => {
  const chatRef = React.useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false); // State to track copy action
  const [isDownloading, setIsDownloading] = useState(false);

  // Function to copy Meeting ID
  const copyMeetingId = () => {
    if (meetingId) {
      navigator.clipboard.writeText(meetingId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000); // Reset after 2s
    }
  };

  // Function to download transcript
  const downloadTranscript = async () => {
    if (!messages || messages.length === 0) {
      alert("No conversation to download yet!");
      return;
    }

    setIsDownloading(true);
    try {
      // Try API download first, fall back to client-side generation
      try {
        const response = await fetch('http://localhost:8001/transcripts/current/text');
        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          
          // Extract filename from response headers if available
          const contentDisposition = response.headers.get('content-disposition');
          let filename = `interview-transcript-${meetingId}-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
          if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
              filename = filenameMatch[1];
            }
          }
          
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
          return;
        }
      } catch (apiError) {
        console.log("API download failed, falling back to client-side generation:", apiError);
      }
      
      // Fallback to client-side transcript generation
      const transcript = generateTextTranscript(messages, meetingId);
      const blob = new Blob([transcript], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `interview-transcript-${meetingId}-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error("Error downloading transcript:", error);
      alert("Failed to download transcript. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  // Function to generate formatted text transcript
  const generateTextTranscript = (messages: Message[], meetingId: string): string => {
    const lines = [];
    lines.push("INTERVIEW TRANSCRIPT");
    lines.push("=".repeat(50));
    lines.push(`Meeting ID: ${meetingId}`);
    lines.push(`Generated: ${new Date().toLocaleString()}`);
    lines.push(`Total Messages: ${messages.length}`);
    lines.push("");
    lines.push("CONVERSATION:");
    lines.push("-".repeat(50));
    lines.push("");

    messages.forEach((message) => {
      const timestamp = new Date(message.timestamp).toLocaleTimeString();
      const speaker = message.isAI ? "AI Interviewer" : "Candidate";
      lines.push(`[${timestamp}] ${speaker}: ${message.text}`);
      lines.push("");
    });

    lines.push("");
    lines.push("=".repeat(50));
    lines.push("End of Transcript");
    
    return lines.join("\n");
  };

  React.useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="w-80 bg-gray-900 border-l border-gray-700 h-full flex flex-col">
      {/* Chat Panel Header with Download Button */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Conversation</h2>
        <button
          onClick={downloadTranscript}
          disabled={!isAIConnected || messages.length === 0 || isDownloading}
          className="flex items-center space-x-2 px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white text-sm transition-colors"
          title="Download conversation transcript"
        >
          {isDownloading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Downloading...</span>
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              <span>Download Transcript</span>
            </>
          )}
        </button>
      </div>

      {/* Meeting ID Display */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <span className="text-gray-300 text-sm">
          Meeting ID: {meetingId || "Loading..."}
        </span>
        <button
          onClick={copyMeetingId}
          className="text-blue-400 hover:text-blue-300 flex items-center space-x-1"
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-400" />
          ) : (
            <Clipboard className="w-4 h-4" />
          )}
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>

      {/* Chat Panel Content */}
      {!isAIConnected ? (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center space-y-4">
            <MessageSquare className="w-12 h-12 text-gray-600 mx-auto" />
            <p className="text-gray-400">
              Chat will start once the AI Copilot joins.
            </p>
          </div>
        </div>
      ) : (
        <div ref={chatRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <p className="text-gray-400 text-center">
              Conversation hasn't started yet.
            </p>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg ${
                  message.isAI ? "bg-blue-900/30 ml-4" : "bg-gray-800 mr-4"
                }`}
              >
                <p className="text-xs text-gray-400 mb-1">
                  {message.isAI ? "AI Copilot" : "You"}
                </p>
                <p className="text-white">{message.text}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
