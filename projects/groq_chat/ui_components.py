# ui_components.py

import streamlit as st


def display_chat_history(messages):
    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            elif msg["type"] == "image_text":
                st.image(msg["image"], caption="Uploaded Image", use_container_width=True)
                st.markdown(msg["content"])

def new_chat_button():
    if st.sidebar.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.image_history = []
        st.rerun()
