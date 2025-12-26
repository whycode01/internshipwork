 PDF Chat with RAG via ChromaDB & Groq LLaMA3 

This is a lean **Streamlit app** to chat with the text of your PDF through an easy-to-use **RAG (Retrieval-Augmented Generation)** pipeline, fueled by:

 **ChromaDB** for vector storage & lookup
 **SentenceTransformers** for text embeddings
 **Groq's LLaMA3-70B** for smart response generation
 **Streamlit** for a web UI to please

 ---

# Features

- Upload any text-based PDF
- Text is chunked and maintained in a local vector database
- Search for applicable chunks based on semantic similarity
- LLaMA3-70B provides responses that are anchored to the PDF content
- Local PDF storage for convenient access
- Persistent ChromaDB storage for performance

---

# Project Structure

rag_chat/
├── app.py # Main Streamlit application
├── requirements.txt # Python dependencies
├── chroma_db/ # ChromaDB persistent storage (auto-created)
└── data/ # Uploaded PDFs (auto-created)

##  Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd pdf_chat_groq
2. Install Requirements
bash
Copy
Edit
pip install -r requirements.txt
3. Add Your Groq API Key
Inside app.py, replace:

python
Copy
Edit
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
with your actual key. You can obtain it from https://console.groq.com/keys.

 Run the Application
bash
Copy
Edit
streamlit run app.py
Visit http://localhost:8501 in your browser.

Notes
Only processes text-based PDFs (scanned/image-based PDFs will not extract text)

Uploaded PDFs are saved in the /data directory

ChromaDB stores its database in /chroma_db

Only pertinent chunks are fed to LLaMA3 to curtail token usage and enhance answer accuracy

Tech Stack
Streamlit

ChromaDB

SentenceTransformers

Groq LLaMA3 API

PyPDF2

Developed By
Gaurav Mishra — Intern
Guided by Harsh Kasana











