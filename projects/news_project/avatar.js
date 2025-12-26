class HeyGenAvatar {
    constructor() {
        this.peerConnection = null;
        this.sessionId = null;
        this.streamId = null;
        this.isSessionActive = false;
    }

    async initialize() {
        try {
            console.log("Step 1: Creating HeyGen token...");
            // Get token from backend
            const tokenResponse = await fetch("/avatar/create-token", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            const tokenData = await tokenResponse.json();
            
            console.log("Token response:", tokenData);
            
            if (!tokenData.data || !tokenData.data.token) {
                throw new Error("Failed to get avatar token: " + JSON.stringify(tokenData));
            }

            const token = tokenData.data.token;
            console.log("Token received:", token);
            
            console.log("Step 2: Creating new session...");
            // Create a new streaming session with the token
            const newSessionResponse = await fetch("/avatar/new-session", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    quality: "high",
                    avatar_name: "Wayne_20240711",
                    voice: {
                        voice_id: "1bd001e7e50f421d891986aad5158bc8"
                    }
                })
            });
            
            const newSessionData = await newSessionResponse.json();
            console.log("New session response:", newSessionData);
            
            // Check for error response
            if (newSessionData.error || newSessionData.code === 10004) {
                const error = new Error(newSessionData.message || "Failed to create session");
                error.code = newSessionData.code;
                error.details = newSessionData;
                throw error;
            }
            
            if (!newSessionData.data || !newSessionData.data.session_id) {
                throw new Error("Failed to create session: " + JSON.stringify(newSessionData));
            }
            
            this.sessionId = newSessionData.data.session_id;
            console.log("Session ID:", this.sessionId);
            
            // HeyGen already provided an SDP offer, we need to use it
            const serverOffer = newSessionData.data.sdp;
            console.log("Server SDP offer received:", serverOffer.type);
            
            console.log("Step 3: Creating WebRTC peer connection...");
            // Create WebRTC peer connection with ICE servers from response
            const iceServers = newSessionData.data.ice_servers2 || newSessionData.data.ice_servers || [
                { urls: "stun:stun.l.google.com:19302" },
                { urls: "stun:stun1.l.google.com:19302" }
            ];
            
            this.peerConnection = new RTCPeerConnection({
                iceServers: iceServers
            });

            // Handle incoming stream
            this.peerConnection.ontrack = (event) => {
                console.log("Received avatar video stream!", event.streams);
                const videoElement = document.getElementById("avatarVideo");
                if (videoElement && event.streams[0]) {
                    videoElement.srcObject = event.streams[0];
                    videoElement.style.display = "block";
                    videoElement.play().then(() => {
                        console.log("✅ Video playback started successfully");
                    }).catch(err => {
                        console.error("Video play error:", err);
                    });
                }
            };

            // Step 4: Set HeyGen's offer as remote description
            console.log("Step 4: Setting remote description (HeyGen's offer)...");
            await this.peerConnection.setRemoteDescription(
                new RTCSessionDescription(serverOffer)
            );

            // Step 5: Create answer to HeyGen's offer
            console.log("Step 5: Creating answer...");
            const answer = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(answer);
            console.log("Local answer set");

            // Wait for ICE gathering to complete
            console.log("Step 6: Waiting for ICE gathering...");
            await this.waitForIceGathering();
            console.log("ICE gathering complete");

            // Step 7: Send our answer back to HeyGen
            console.log("Step 7: Sending answer to HeyGen...");
            const startResponse = await fetch("/avatar/start-session", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    sdp: {
                        type: this.peerConnection.localDescription.type,
                        sdp: this.peerConnection.localDescription.sdp
                    },
                    session_id: this.sessionId
                })
            });

            const startData = await startResponse.json();
            console.log("Start session response:", startData);
            
            if (startData.code === 100 || (startData.data && startData.message === 'success')) {
                this.isSessionActive = true;
                console.log("✅ Avatar session started successfully!");
                return true;
            }
            
            throw new Error("Failed to start avatar session: " + JSON.stringify(startData));
        } catch (error) {
            console.error("Avatar initialization error:", error);
            return false;
        }
    }

    waitForIceGathering() {
        return new Promise((resolve) => {
            if (this.peerConnection.iceGatheringState === "complete") {
                resolve();
            } else {
                const checkState = () => {
                    if (this.peerConnection.iceGatheringState === "complete") {
                        this.peerConnection.removeEventListener("icegatheringstatechange", checkState);
                        resolve();
                    }
                };
                this.peerConnection.addEventListener("icegatheringstatechange", checkState);
            }
        });
    }

    async speak(text) {
        if (!this.isSessionActive) {
            console.error("Avatar session not active");
            return false;
        }

        try {
            // Create data channel for text input
            const dataChannel = this.peerConnection.createDataChannel("text_input");
            
            dataChannel.onopen = () => {
                console.log("Sending text to avatar:", text);
                dataChannel.send(JSON.stringify({
                    type: "text",
                    text: text
                }));
            };

            return true;
        } catch (error) {
            console.error("Avatar speak error:", error);
            return false;
        }
    }

    async close() {
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }
        this.isSessionActive = false;
        this.sessionId = null;
    }
}

// Export for use in script.js
window.HeyGenAvatar = HeyGenAvatar;
