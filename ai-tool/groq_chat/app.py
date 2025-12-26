import requests
import streamlit as st

GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


AVAILABLE_MODELS = {
    "llama3-8b-8192": "LLaMA 3 - 8B - Fast, lightweight general-purpose model.",
    "llama3-70b-8192": "LLaMA 3 - 70B - High-performance, large context model.",
    "gemma-7b-it": "Gemma 7B - Instruction-tuned model optimized for chat."
}

st.set_page_config(page_title="Groq LLM Chat with Model Selector")
st.title("💬 Groq LLM Chatbot")


model_display_names = [f"{model} - {desc}" for model, desc in AVAILABLE_MODELS.items()]

display_to_model = {
    f"{model} - {desc}": model for model, desc in AVAILABLE_MODELS.items()
}


selected_display_name = st.selectbox("Choose LLM Model", model_display_names)
selected_model = display_to_model[selected_display_name]

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").markdown(msg["content"])


if prompt := st.chat_input("Say something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    payload = {
        "model": selected_model,
        "messages": st.session_state.messages
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").markdown(reply)

    except Exception as e:
        st.error(f"Error: {e}")
