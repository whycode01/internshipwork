import os

import chromadb
import PyPDF2
import requests
import streamlit as st
from sentence_transformers import SentenceTransformer

# ------------------ CONFIG ------------------
st.set_page_config(page_title="PDF Chat with RAG (Groq LLaMA3)", layout="wide")

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

PERSIST_DIRECTORY = "chroma_db"
DATA_DIRECTORY = "data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "pdf_collection"

# ------------------ INITIALIZATION ------------------
os.makedirs(DATA_DIRECTORY, exist_ok=True)  # Auto-create 'data' folder if missing

embedder = SentenceTransformer(EMBEDDING_MODEL)

chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

if COLLECTION_NAME not in [col.name for col in chroma_client.list_collections()]:
    collection = chroma_client.create_collection(name=COLLECTION_NAME)
else:
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

# ------------------ PDF PROCESSING ------------------
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    return chunks

def store_pdf_chunks(pdf_text, pdf_name):
    chunks = chunk_text(pdf_text, chunk_size=500, overlap=50)
    
    if not chunks:
        st.warning(f"No valid text extracted from {pdf_name}. Skipping storage.")
        return
    
    embeddings = embedder.encode(chunks).tolist()
    
    if not embeddings:
        st.warning(f"Embeddings generation failed for {pdf_name}. Skipping storage.")
        return
    
    ids = [f"{pdf_name}_{i}" for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )

# ------------------ RAG Retrieval ------------------
def retrieve_relevant_chunks(query, top_k=3):
    query_embedding = embedder.encode([query]).tolist()[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    print(results)
    
    if "documents" in results and results["documents"]:
        return results["documents"][0]
    return []

# ------------------ GROQ Completion (LLaMA3) ------------------
def generate_answer_with_groq(question, context_chunks):
    context = "\n".join(context_chunks)
    
    prompt = f"""You are an expert assistant answering questions based on provided PDF content.
PDF Content:
{context}

Question:
{question}

Answer:"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant answering questions based on provided PDF content."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        st.error(f"Groq API Error: {response.text}")
        return "Error generating answer."

# ------------------ STREAMLIT UI ------------------
st.title("📄 Chat with your PDF (RAG + Groq LLaMA3, No LangChain)")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
if uploaded_file:
    pdf_path = os.path.join(DATA_DIRECTORY, uploaded_file.name)
    
    # Save uploaded file to 'data' folder
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"{uploaded_file.name} uploaded and saved successfully.")
    
    pdf_text = extract_text_from_pdf(pdf_path)
    
    if not pdf_text.strip():
        st.warning(f"No text could be extracted from {uploaded_file.name}. It may be scanned or image-based.")
    else:
        store_pdf_chunks(pdf_text, uploaded_file.name)
        st.info(f"Processed and stored chunks from {uploaded_file.name}")

st.divider()
st.subheader("Ask Questions Based on Uploaded PDFs")

query = st.text_input("Enter your question:")
if st.button("Get Answer") and query:
    with st.spinner("Retrieving relevant chunks and generating answer..."):
        relevant_chunks = retrieve_relevant_chunks(query)
        
        if relevant_chunks:
            answer = generate_answer_with_groq(query, relevant_chunks)
            st.success("Answer:")
            st.write(answer)
            
            with st.expander("Relevant Chunks Used"):
                for i, chunk in enumerate(relevant_chunks):
                    st.write(f"**Chunk {i+1}:** {chunk}")
        else:
            st.warning("No relevant content found. Try a different question.")
