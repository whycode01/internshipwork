

import requests
import streamlit as st
from groq import Groq

from chat_logic import build_chat_input
from config import GROQ_API_KEY
from ui_components import display_chat_history, new_chat_button


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = ""

if not st.session_state.authenticated:
    st.set_page_config(page_title="Groq Chat Login")
    st.subheader("Login to use the chat")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            response = requests.post(
                "http://localhost:8000/login",
                data={"username": username, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                st.session_state.token = response.json()["access_token"]
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Login failed.")
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()


client = Groq(api_key=GROQ_API_KEY)
st.set_page_config(page_title="Groq Chat with Image Upload", layout="centered")
st.title("Groq Chat with Image-Aware Memory")
new_chat_button()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "image_history" not in st.session_state:
    st.session_state.image_history = []

display_chat_history(st.session_state.messages)

prompt = st.chat_input(
    "Enter a message or upload an image",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"],
)

if prompt:
    user_text = prompt.text.strip() if prompt.text else ""
    user_file = prompt.files[0].read() if prompt.files else None

    model, user_msg, img_bytes, clean_text = build_chat_input(
        user_text, user_file, st.session_state.image_history
    )

    
    if user_file:
        st.session_state.image_history.append(user_msg)
        st.session_state.messages.append({
            "role": "user", "type": "image_text", "content": clean_text, "image": img_bytes
        })
        with st.chat_message("user"):
            st.image(img_bytes, caption="Uploaded Image", use_container_width=True)
            st.markdown(clean_text)
    else:
        st.session_state.messages.append({
            "role": "user", "type": "text", "content": clean_text
        })
        with st.chat_message("user"):
            st.markdown(clean_text)

    chat_input = [user_msg] if model == "llama3-70b-8192" else st.session_state.image_history + [user_msg]

    try:
        response = client.chat.completions.create(
            messages=chat_input,
            model=model,
        ).choices[0].message.content
    except Exception as e:
        response = f"Error: {e}"

    st.session_state.messages.append({
        "role": "assistant", "type": "text", "content": response
    })
    with st.chat_message("assistant"):
        st.markdown(response)
