import { MeetingProvider } from "@videosdk.live/react-sdk";
import { Bot } from "lucide-react";
import React, { Suspense } from "react";
import toast, { Toaster } from "react-hot-toast";
import { InteractionOptions } from "./components/InteractionOptions";

// Lazy load the MeetingPopup component to reduce initial bundle size
const MeetingPopup = React.lazy(() => import("./components/MeetingPopup").then(module => ({ default: module.MeetingPopup })));

function App() {
  const [meetingId, setMeetingId] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [useVideo, setUseVideo] = React.useState(false);

  const createMeeting = async () => {
    try {
      setIsLoading(true);
      const response = await fetch("https://api.videosdk.live/v2/rooms", {
        method: "POST",
        headers: {
          Authorization: import.meta.env.VITE_APP_AUTH_TOKEN,
          "Content-Type": "application/json",
        },
      });

      const { roomId } = await response.json();
      setMeetingId(roomId);
    } catch (error) {
      toast.error("Failed to create meeting. Please try again.");
      console.error("Error creating meeting:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = async (withVideo: boolean) => {
    setUseVideo(withVideo);
    await createMeeting();
  };

  const handleClose = () => {
    setMeetingId(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <Toaster position="top-center" />

      {!meetingId ? (
        <div className="text-center max-w-2xl mx-auto px-4">
          <div className="mb-24 relative">
            <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-32 h-32 bg-blue-500/10 rounded-full flex items-center justify-center">
              <Bot className="w-16 h-16 text-blue-400" />
            </div>
            {/* <h1 className="text-4xl font-bold text-white mb-4">
              AI Copilot Assistant
            </h1>
            <p className="text-gray-400 text-lg max-w-xl mx-auto">
              Start a conversation with our AI Copilot. Choose your preferred mode of interaction below.
            </p> */}
          </div>
          <InteractionOptions onStart={handleStart} isLoading={isLoading} />
        </div>
      ) : (
        <MeetingProvider
          config={{
            meetingId,
            micEnabled: true,
            webcamEnabled: useVideo,
            name: "User",
            debugMode: true,
          }}
          token={import.meta.env.VITE_APP_AUTH_TOKEN}
          joinWithoutUserInteraction
        >
          <Suspense fallback={
            <div className="h-full flex items-center justify-center">
              <div className="text-center space-y-4">
                <Bot className="w-12 h-12 text-blue-500 animate-spin mx-auto" />
                <p className="text-white text-lg">Loading meeting interface...</p>
              </div>
            </div>
          }>
            <MeetingPopup onClose={handleClose} meetingId={meetingId} />
          </Suspense>
        </MeetingProvider>
      )}
    </div>
  );
}

export default App;
