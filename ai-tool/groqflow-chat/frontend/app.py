import uuid

import requests
import streamlit as st
from config import BACKEND_URL

st.set_page_config(page_title="Groq Multimodal Chat", layout="wide")

CHAT_API = f"{BACKEND_URL}/chat"

# -------------------------------
# 🔐 AUTH SECTION
# -------------------------------
st.sidebar.title("🔐 Authentication")

if "token" not in st.session_state:
    st.session_state.token = None

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_message_sent" not in st.session_state:
    st.session_state.last_message_sent = None

def login_or_signup(mode="login"):
    username = st.sidebar.text_input("Username", key=f"{mode}_username")
    password = st.sidebar.text_input("Password", type="password", key=f"{mode}_password")

    if st.sidebar.button("Login" if mode == "login" else "Sign Up"):
        try:
            url = f"{BACKEND_URL}/login" if mode == "login" else f"{BACKEND_URL}/signup"
            response = requests.post(url, data={"username": username, "password": password})

            if response.status_code == 200:
                if mode == "login":
                    st.session_state.token = response.json()["access_token"]
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.chat_history = []
                    st.session_state.username = username
                    st.session_state.last_message_sent = None  # ✅ reset
                    st.success("✅ Logged in successfully")
                    st.rerun()
                else:
                    st.success("✅ Sign up successful. Please log in.")
            else:
                st.error(response.json().get("detail", "Error"))
        except Exception as e:
            st.error(f"Error: {e}")

if st.session_state.token is None:
    auth_tab = st.sidebar.radio("Choose:", ["Login", "Sign Up"])
    login_or_signup(mode="login" if auth_tab == "Login" else "signup")
    st.stop()

if st.sidebar.button("🚪 Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# -------------------------------
# CHAT SECTION
# -------------------------------
st.title("💬 Groq Chat (Multimodal)")
headers = {"Authorization": f"Bearer {st.session_state.token}"}

try:
    session_response = requests.get(f"{CHAT_API}/sessions", headers=headers)
    all_sessions = session_response.json() if session_response.status_code == 200 else []
except Exception:
    all_sessions = []

st.sidebar.title("📚 Chat Sessions")

if st.sidebar.button("🆕 New Chat"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.last_message_sent = None  # ✅ reset

for sess in all_sessions:
    session_id = sess["session_id"]
    title = sess.get("title") or session_id[:8]

    with st.sidebar.expander(f"🗂️ {title}", expanded=False):
        if st.button("📂 Open", key=f"open_{session_id}"):
            st.session_state.session_id = session_id
            try:
                r = requests.get(f"{CHAT_API}/history", params={"session_id": session_id}, headers=headers)
                if r.status_code == 200:
                    history = r.json()
                    for msg in history:
                        if msg["type"] == "image_text":
                            msg["image"] = f"{CHAT_API}/images/{msg['image_path']}"
                    st.session_state.chat_history = history
                    st.session_state.last_message_sent = None  # ✅ reset
            except Exception as e:
                st.warning(f"Failed to load history: {e}")

        new_name = st.text_input("✏️ Rename", key=f"rename_input_{session_id}", value=title)
        if st.button("✅ Rename", key=f"rename_btn_{session_id}"):
            requests.post(f"{CHAT_API}/rename_session", data={
                "session_id": session_id, "new_title": new_name
            }, headers=headers)
            st.rerun()

        if st.button("🗑️ Delete", key=f"delete_btn_{session_id}"):
            requests.delete(f"{CHAT_API}/delete_session", params={"session_id": session_id}, headers=headers)
            st.rerun()

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg["type"] == "text":
            st.markdown(msg["content"])
        elif msg["type"] == "image":
            if msg.get("image"):
                st.image(msg["image"], use_container_width=True)
        elif msg["type"] == "image_text":
            if msg.get("image"):
                st.image(msg["image"], use_container_width=True)
            st.markdown(msg["content"])

# -------------------------------
# Chat Input Handling
# -------------------------------
prompt = st.chat_input(
    "Say something and/or attach an image",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"]
)

if prompt and prompt.text != st.session_state.last_message_sent:
    user_text = prompt.text.strip() if prompt.text else ""
    user_file = prompt.files[0] if prompt.files else None

    if not user_text and not user_file:
        st.warning("Please enter a message or upload an image.")
        st.stop()

    st.session_state.last_message_sent = prompt.text  # ✅ update tracker

    session_id = st.session_state.session_id
    msg_type = "image_text" if user_file and user_text else "image" if user_file else "text"

    with st.chat_message("user"):
        if user_file:
            st.image(user_file, use_container_width=True)
        if user_text:
            st.markdown(user_text)

    user_msg = {
        "role": "user",
        "type": msg_type,
        "content": user_text if user_text else "Describe this image.",
        "image": None
    }
    st.session_state.chat_history.append(user_msg)

    try:
        if msg_type == "text":
            response = requests.post(
                f"{CHAT_API}/text",
                data={"message": user_text, "session_id": session_id},
                headers=headers
            )
        else:
            response = requests.post(
                f"{CHAT_API}/image",
                data={"message": user_text or "Describe this image.", "session_id": session_id},
                files={"image": user_file},
                headers=headers
            )

        if response.status_code == 200:
            data = response.json()
            reply = data.get("response", "No reply received.")
            image_filename = data.get("image_filename")

            with st.chat_message("assistant"):
                st.markdown(reply)

            st.session_state.chat_history.append({
                "role": "assistant",
                "type": "text",
                "content": reply,
                "image": None
            })

            if msg_type in ["image", "image_text"] and image_filename:
                st.session_state.chat_history[-2]["image"] = f"{CHAT_API}/images/{image_filename}"

        else:
            st.error(f"Backend error: {response.status_code} - {response.text}")

    except Exception as e:
        st.error(f"Error communicating with backend: {e}")
