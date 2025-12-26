from typing import List
from openai import OpenAI
from config import GROQ_API_KEY, LLAMA_MODEL, LLAMA_BASE_URL

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz

# --- Config ---
CHUNK_SIZE = 3000
OVERLAP = CHUNK_SIZE // 3
TOP_K = 12
FUZZ_THRESHOLD = 90

# --- Chunking ---
def chunk_text(text: str) -> List[str]:
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + CHUNK_SIZE, len(text))
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        i += CHUNK_SIZE - OVERLAP
    return chunks

# --- Retrieval ---
def retrieve_top_k(query: str, chunks: List[str], k: int = TOP_K) -> List[str]:
    vectorizer = TfidfVectorizer().fit(chunks + [query])
    vectors = vectorizer.transform(chunks + [query])
    sim_scores = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
    top_indices = sim_scores.argsort()[::-1][:k]
    return [chunks[i] for i in top_indices]

# --- LLaMA Client ---
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=LLAMA_BASE_URL,
    timeout=30,
)

def _llama(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=768,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLAMA_ERROR: {e}"

# --- Fuzzy Duplicate Checker ---
def is_duplicate(new_q: str, existing: set) -> bool:
    for q in existing:
        if fuzz.ratio(new_q.lower(), q.lower()) >= FUZZ_THRESHOLD:
            return True
    return False

# --- Flashcard Generator ---
def generate_flashcards(full_text: str, existing_questions: List[str] = []) -> List[dict]:
    chunks = chunk_text(full_text)
    seen_questions = set(existing_questions)
    flashcards = []

    for chunk in chunks:
        top_chunks = retrieve_top_k(chunk, chunks)
        context = "\n\n".join(top_chunks)
        if len(context) > 7000:
            context = context[:7000]

        previous_qs = "\n".join(f"- {q}" for q in seen_questions if q.strip())

        prompt = (
            "You are a highly skilled teaching assistant.\n"
            "Based on the following content, generate EXACTLY THREE NEW high-quality flashcards.\n"
            "Do NOT repeat any of these previously generated questions:\n"
            f"{previous_qs if previous_qs else 'None'}\n\n"
            "Each flashcard must be formatted like:\n"
            "`Question?|Answer.`\n\n"
            f"CONTENT:\n{context}"
        )

        result = _llama(prompt)
        if result.startswith("LLAMA_ERROR"):
            print(result)
            continue

        for line in result.splitlines():
            if "|" not in line:
                continue
            q, a = [x.strip() for x in line.split("|", 1)]
            if q and a and not is_duplicate(q, seen_questions):
                seen_questions.add(q)
                flashcards.append({"question": q, "answer": a})

    return flashcards

# --- Answer Contextual Matching ---
def match_answer(question: str, user_answer: str, correct_answer: str) -> bool:
    prompt = f"""
You are a helpful assistant. You are given a question, the user's answer, and the correct answer.

Compare the user's answer with the correct answer **contextually** (not line-by-line). 
If it is a valid and contextually correct answer, return only "yes". 
If it is not contextually matching, return only "no".

Question: {question}
User Answer: {user_answer}
Correct Answer: {correct_answer}

Is the user's answer correct?
""".strip()

    response = _llama(prompt).strip().lower()
    return "yes" in response
