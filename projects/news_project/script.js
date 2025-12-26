const newsContainer = document.getElementById("newsContainer");
const fetchBtn = document.getElementById("fetchNews");
const playAllBtn = document.getElementById("playAll");
const stopAllBtn = document.getElementById("stopAll");
const voiceBtn = document.getElementById("voiceCommand");
const speechStatus = document.getElementById("speechStatus");
const startAvatarBtn = document.getElementById("startAvatar");
const stopAvatarBtn = document.getElementById("stopAvatar");
const avatarVideo = document.getElementById("avatarVideo");
const avatarLoading = document.getElementById("avatarLoading");
const avatarPlaceholder = document.getElementById("avatarPlaceholder");

let headlines = [];
let currentUtterance = null;
let avatar = null;
let useAvatar = false;

// ---------------------- Fetch News ----------------------

async function fetchNews() {
    const res = await fetch("/news/india");
    headlines = await res.json();
    renderNews();
}

function renderNews() {
    newsContainer.innerHTML = "";
    headlines.forEach(item => {
        const card = document.createElement("news-card");
        card.setAttribute("title", item.title);
        card.setAttribute("source", item.source);
        newsContainer.appendChild(card);
    });
}

// ---------------------- HeyGen Avatar Management ----------------------

async function startAvatarSession() {
    startAvatarBtn.disabled = true;
    avatarPlaceholder.classList.add("hidden");
    avatarLoading.classList.remove("hidden");
    
    try {
        avatar = new HeyGenAvatar();
        const success = await avatar.initialize();
        
        if (success) {
            avatarLoading.classList.add("hidden");
            useAvatar = true;
            startAvatarBtn.classList.add("hidden");
            stopAvatarBtn.classList.remove("hidden");
            console.log("Avatar initialized successfully");
        } else {
            throw new Error("Failed to initialize avatar");
        }
    } catch (error) {
        console.error("Avatar error:", error);
        
        // Show user-friendly error message
        let errorMsg = "Failed to start avatar.\n\n";
        if (error.message && error.message.includes("Concurrent limit")) {
            errorMsg += "⚠️ HeyGen concurrent session limit reached.\n\n" +
                       "This happens when:\n" +
                       "• Another avatar session is already running\n" +
                       "• Previous session wasn't properly closed\n\n" +
                       "Solutions:\n" +
                       "1. Wait a few minutes and try again\n" +
                       "2. Use audio-only mode (ElevenLabs TTS)\n" +
                       "3. Upgrade your HeyGen plan for more sessions\n\n" +
                       "Switching to audio-only mode...";
        } else {
            errorMsg += "Switching to audio-only mode with ElevenLabs TTS.";
        }
        
        alert(errorMsg);
        avatarLoading.classList.add("hidden");
        avatarPlaceholder.classList.remove("hidden");
        
        // Show message on placeholder
        avatarPlaceholder.innerHTML = `
            <div class="text-center" style="text-align: center; padding: 2rem;">
                <i data-feather="alert-circle" class="mx-auto mb-4" style="width: 64px; height: 64px; margin: 0 auto 1rem; color: #fbbf24;"></i>
                <p class="text-xl font-semibold mb-4" style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem;">Avatar Unavailable</p>
                <p class="text-sm mb-4" style="font-size: 0.875rem; margin-bottom: 1rem;">Using audio-only mode</p>
                <p class="text-xs" style="font-size: 0.75rem; opacity: 0.8;">HeyGen session limit reached. Audio will play without video.</p>
            </div>
        `;
        feather.replace();
        
        startAvatarBtn.disabled = false;
        startAvatarBtn.textContent = "Audio Mode Only";
    }
}

async function stopAvatarSession() {
    if (avatar) {
        await avatar.close();
        avatar = null;
    }
    useAvatar = false;
    avatarVideo.srcObject = null;
    avatarPlaceholder.classList.remove("hidden");
    startAvatarBtn.classList.remove("hidden");
    stopAvatarBtn.classList.add("hidden");
    startAvatarBtn.disabled = false;
}

// ---------------------- TTS (Text-to-Speech) with Avatar or ElevenLabs ----------------------

let audioQueue = [];
let currentAudio = null;
let isPlaying = false;

async function speakAll() {
    stopSpeaking();
    
    if (headlines.length === 0) {
        alert("No headlines to read. Please fetch news first.");
        return;
    }
    
    speechStatus.classList.remove("hidden");
    isPlaying = true;
    
    for (const item of headlines) {
        if (!isPlaying) break;
        
        try {
            if (useAvatar && avatar && avatar.isSessionActive) {
                // Use HeyGen avatar to speak
                await avatar.speak(item.title);
                // Wait a bit for the avatar to finish speaking
                await new Promise(resolve => setTimeout(resolve, item.title.length * 50));
            } else {
                // Fallback to ElevenLabs audio
                const response = await fetch("/tts/speak", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ text: item.title })
                });
                
                if (!response.ok) {
                    console.error("TTS failed for:", item.title);
                    continue;
                }
                
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                
                await playAudio(audioUrl);
            }
            
        } catch (error) {
            console.error("Error speaking headline:", error);
        }
    }
    
    speechStatus.classList.add("hidden");
    isPlaying = false;
}

function playAudio(url) {
    return new Promise((resolve, reject) => {
        currentAudio = new Audio(url);
        
        currentAudio.onended = () => {
            URL.revokeObjectURL(url);
            resolve();
        };
        
        currentAudio.onerror = (error) => {
            console.error("Audio playback error:", error);
            URL.revokeObjectURL(url);
            reject(error);
        };
        
        currentAudio.play().catch(reject);
    });
}

function stopSpeaking() {
    isPlaying = false;
    
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
    
    speechStatus.classList.add("hidden");
}

// ---------------------- STT (Speech-to-Text) ----------------------

function startSTT() {
    if (!("webkitSpeechRecognition" in window)) {
        alert("Speech Recognition not supported in this browser");
        return;
    }

    const recognizer = new webkitSpeechRecognition();
    recognizer.lang = "en-IN";
    recognizer.continuous = false;

    recognizer.onresult = async (event) => {
        const text = event.results[0][0].transcript.toLowerCase();
        console.log("Voice command:", text);

        if (text.includes("refresh")) {
            await fetchNews();
        }
        if (text.includes("play")) {
            speakAll();
        }
        if (text.includes("stop")) {
            stopSpeaking();
        }

        // (optional) fetch specific state news
        const states = ["maharashtra", "karnataka", "gujarat", "tamil nadu", "kerala", "rajasthan"];
        for (let st of states) {
            if (text.includes(st)) {
                const res = await fetch(`/news/state/${st}`);
                const d = await res.json();
                headlines = d;
                renderNews();
                break;
            }
        }
    };

    recognizer.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
    };

    recognizer.start();
}

// ---------------------- Events ----------------------

fetchBtn.addEventListener("click", fetchNews);
playAllBtn.addEventListener("click", speakAll);
stopAllBtn.addEventListener("click", stopSpeaking);
voiceBtn.addEventListener("click", startSTT);
startAvatarBtn.addEventListener("click", startAvatarSession);
stopAvatarBtn.addEventListener("click", stopAvatarSession);

// Auto load on start
fetchNews();
