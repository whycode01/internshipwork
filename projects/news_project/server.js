import axios from "axios";
import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import { fetchIndianHeadlines, fetchStateNews } from "./newsService.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(".")); // serve index.html and frontend files

app.get("/news/india", async (req, res) => {
    try {
        const news = await fetchIndianHeadlines();
        res.json(news);
    } catch (e) {
        res.status(500).json({ error: "Failed to fetch India news" });
    }
});

app.get("/news/state/:name", async (req, res) => {
    try {
        const { name } = req.params;
        const news = await fetchStateNews(name);
        res.json(news);
    } catch (e) {
        res.status(500).json({ error: "Failed to fetch state news" });
    }
});

// Test endpoint to verify ElevenLabs API key
app.get("/tts/test", async (req, res) => {
    try {
        const apiKey = process.env.ELEVENLABS_API_KEY?.trim();
        if (!apiKey) {
            return res.json({ status: "error", message: "API key not configured" });
        }
        
        // Test by getting user info
        const response = await axios.get("https://api.elevenlabs.io/v1/user", {
            headers: { "xi-api-key": apiKey }
        });
        
        res.json({ status: "success", message: "API key is valid", data: response.data });
    } catch (e) {
        res.json({ 
            status: "error", 
            message: e.response?.data?.detail || e.message,
            statusCode: e.response?.status 
        });
    }
});

app.post("/tts/speak", async (req, res) => {
    try {
        const { text } = req.body;
        
        // Debug: Check if API key is loaded
        const apiKey = process.env.ELEVENLABS_API_KEY?.trim();
        if (!apiKey) {
            console.error("ELEVENLABS_API_KEY is not set in .env file");
            return res.status(500).json({ error: "API key not configured" });
        }
        
        // ElevenLabs API endpoint for text-to-speech
        // Using free-tier compatible voice and model
        const voiceId = "pNInz6obpgDQGcFmaJgB"; // Adam voice (free tier)
        const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`;
        
        const response = await axios.post(
            url,
            {
                text: text,
                model_id: "eleven_turbo_v2_5", // Free tier compatible model
                voice_settings: {
                    stability: 0.5,
                    similarity_boost: 0.75
                }
            },
            {
                headers: {
                    "Accept": "audio/mpeg",
                    "xi-api-key": apiKey,
                    "Content-Type": "application/json"
                },
                responseType: "arraybuffer"
            }
        );
        
        res.set("Content-Type", "audio/mpeg");
        res.send(Buffer.from(response.data));
    } catch (e) {
        console.error("ElevenLabs TTS error:", e.response?.data || e.message);
        console.error("Status:", e.response?.status);
        console.error("API Key (first 10 chars):", process.env.ELEVENLABS_API_KEY?.substring(0, 10));
        res.status(500).json({ error: "Failed to generate speech" });
    }
});

// HeyGen Interactive Avatar endpoints
app.post("/avatar/create-token", async (req, res) => {
    try {
        const apiKey = process.env.HEYGEN_API_KEY?.trim();
        if (!apiKey) {
            return res.status(500).json({ error: "HeyGen API key not configured" });
        }

        console.log("Creating HeyGen streaming token...");
        const response = await axios.post(
            "https://api.heygen.com/v1/streaming.create_token",
            {},
            {
                headers: {
                    "x-api-key": apiKey,
                    "Content-Type": "application/json"
                }
            }
        );

        console.log("Token created successfully:", response.data);
        res.json(response.data);
    } catch (e) {
        console.error("HeyGen token error:", e.response?.data || e.message);
        res.status(500).json({ error: "Failed to create avatar token", details: e.response?.data || e.message });
    }
});

app.post("/avatar/new-session", async (req, res) => {
    try {
        const apiKey = process.env.HEYGEN_API_KEY?.trim();
        const { quality, avatar_name, voice } = req.body;

        console.log("Creating new HeyGen session...");
        const response = await axios.post(
            "https://api.heygen.com/v1/streaming.new",
            {
                quality: quality || "high",
                avatar_name: avatar_name || "Wayne_20240711",
                voice: voice || { voice_id: "1bd001e7e50f421d891986aad5158bc8" }
            },
            {
                headers: {
                    "x-api-key": apiKey,
                    "Content-Type": "application/json"
                }
            }
        );

        console.log("Session created successfully:", response.data);
        res.json(response.data);
    } catch (e) {
        console.error("HeyGen new session error:", e.response?.data || e.message);
        
        // Return the error details to the frontend
        const errorData = e.response?.data || { message: e.message };
        res.status(e.response?.status || 500).json({ 
            error: true,
            code: errorData.code || 500,
            message: errorData.message || "Failed to create new session",
            details: errorData
        });
    }
});

app.post("/avatar/start-session", async (req, res) => {
    try {
        const { sdp, session_id } = req.body;
        const apiKey = process.env.HEYGEN_API_KEY?.trim();

        console.log("Starting HeyGen session with session_id:", session_id);
        console.log("SDP type:", sdp?.type);

        const response = await axios.post(
            "https://api.heygen.com/v1/streaming.start",
            {
                sdp,
                session_id
            },
            {
                headers: {
                    "x-api-key": apiKey,
                    "Content-Type": "application/json"
                }
            }
        );

        console.log("Session started successfully:", response.data);
        res.json(response.data);
    } catch (e) {
        console.error("HeyGen start session error:", e.response?.data || e.message);
        console.error("Full error:", e);
        res.status(500).json({ 
            error: "Failed to start avatar session",
            details: e.response?.data || e.message 
        });
    }
});

app.listen(5000, () => console.log("Backend running at http://localhost:5000"));
