# main.py

import torch
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from transformers import pipeline
import io
import librosa
import re
import requests 
import uuid 
from pydantic import BaseModel
import sqlite3
from passlib.context import CryptContext
import os # Import the os library

# --- Password Hashing Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Database Setup ---
# --- FIXED: Use an environment variable for the database path for deployment ---
# This reads the DATABASE_PATH from the Dockerfile. If it's not found (e.g., running locally),
# it defaults to creating the file in the current directory.
DATABASE_NAME = os.getenv("DATABASE_PATH", "lexisynth.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_user_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Create the table when the app starts
create_user_table()


# --- Pydantic Models for API ---
class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class QuestionRequest(BaseModel):
    question: str
    context: str

# --- Security Functions ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# --- 1. Initialize the FastAPI app ---
app = FastAPI(
    title="Lexi-Synth API",
    description="An AI-powered legal analysis tool with user authentication."
)

# ... (The rest of your AI model loading and helper functions remain the same) ...
print("Loading all AI models...")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6", device=0 if torch.cuda.is_available() else -1)
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple", device=0 if torch.cuda.is_available() else -1)
asr_pipeline = pipeline("automatic-speech-recognition", model="openai/whisper-base.en", return_timestamps="word", device=0 if torch.cuda.is_available() else -1)
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad", device=0 if torch.cuda.is_available() else -1)
print("All models loaded.")

def find_legal_citations(text: str):
    citation_pattern = re.compile(r'((?:[A-Z][a-zA-Z\s]+)+Act\s+§\s+[\d\(\),\s]+)|(\d+\s+C\.F\.R\.\s+§\s+[\d\.]+)')
    matches = citation_pattern.findall(text)
    return ["".join(match) for match in matches]

def fetch_citation_text(citation: str):
    if "16 C.F.R. § 444.1" in citation: return "Mock text for 16 C.F.R. § 444.1..."
    if "Uniform Trade Secrets Act" in citation: return "Mock text for the Uniform Trade Secrets Act..."
    return f"Full text for '{citation}' could not be retrieved."

def format_transcription(chunks):
    full_text = ""
    for chunk in chunks:
        start_str = f"[{chunk['timestamp'][0]:07.3f}]"
        full_text += f"{start_str} {chunk['text']}"
    return full_text.strip()

def analyze_text(text: str):
    max_chunk_length = 450
    words = text.split()
    chunks = [" ".join(words[i:i + max_chunk_length]) for i in range(0, len(words), max_chunk_length)]
    if not chunks: chunks.append(text)
    
    summaries = summarizer(chunks, max_length=100, min_length=20, do_sample=False)
    summary_text = " ".join([s['summary_text'] for s in summaries])
    
    ner_results_list = ner_pipeline(chunks)
    ner_results = [entity for sublist in ner_results_list for entity in sublist]
    seen_entities = set()
    cleaned_entities = []
    for entity in ner_results:
        entity_tuple = (entity['word'], entity['entity_group'])
        if entity_tuple not in seen_entities:
            cleaned_entities.append({"entity_group": entity["entity_group"], "score": float(entity["score"]), "word": entity["word"]})
            seen_entities.add(entity_tuple)

    found_citations = find_legal_citations(text)
    citations_with_text = [{"citation": cit, "text": fetch_citation_text(cit)} for cit in found_citations]
    
    return {"analysis_id": str(uuid.uuid4()), "summary": summary_text, "entities": cleaned_entities, "citations": citations_with_text, "original_text": text}


# --- 4. Define API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to Lexi-Synth. The API is running."}

# --- User Authentication Endpoints ---
@app.post("/register/")
def register_user(user: UserCreate):
    conn = get_db_connection()
    hashed_password = get_password_hash(user.password)
    try:
        conn.execute(
            "INSERT INTO users (name, username, email, hashed_password) VALUES (?, ?, ?, ?)",
            (user.name, user.username, user.email, hashed_password),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    finally:
        conn.close()
    return {"message": "User registered successfully"}

@app.post("/login/")
def login_user(user: UserLogin):
    conn = get_db_connection()
    db_user = conn.execute("SELECT * FROM users WHERE username = ?", (user.username,)).fetchone()
    conn.close()
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": "Login successful", "user": {"username": db_user["username"], "name": db_user["name"]}}


# --- Analysis Endpoints ---
@app.post("/analyze-text/")
async def analyze_text_file(file: UploadFile = File(...)):
    contents = await file.read()
    text = contents.decode("utf-8", errors="replace")
    return {"filename": file.filename, **analyze_text(text)}

@app.post("/analyze-audio/")
async def analyze_audio_file(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    audio, _ = librosa.load(io.BytesIO(audio_bytes), sr=16000)
    transcription_result = asr_pipeline({"sampling_rate": 16000, "raw": audio})
    analysis_results = analyze_text(transcription_result['text'])
    analysis_results['original_text'] = format_transcription(transcription_result['chunks'])
    return {"filename": file.filename, **analysis_results}

@app.post("/answer-question/")
async def answer_question(request: QuestionRequest):
    result = qa_pipeline(question=request.question, context=request.context)
    return {"answer": result['answer'], "score": result['score']}
