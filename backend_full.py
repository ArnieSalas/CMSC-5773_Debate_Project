from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import requests
from typing import List

# --- LLM Setup ---
BASE_URL = "https://minerals-campaigns-anger-networking.trycloudflare.com"  # your tunnel URL
API_KEY = "sk-local"  # dummy key for vLLM

def query_llm(prompt):
    payload = {
        "model": "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 256
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# --- SQLAlchemy setup ---
DATABASE_URL = "sqlite:///./chat.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---
class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    sender = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- FastAPI app ---
app = FastAPI()

# --- Adding CORS for different ports ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to ["http://localhost:5173"] if preferred
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class DebateInput(BaseModel):
    session_id: int
    starting_message: str
    persona_list: List[str]
    rounds: int

class MessageInput(BaseModel):
    session_id: int
    persona_name: str
    user_message: str

# --- Debate Endpoint ---
@app.post("/debate/")
def start_debate(input: DebateInput):
    db = next(get_db())
    session = db.query(Session).filter(Session.id == input.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    debate_history = []
    current_message = input.starting_message

    for round_num in range(input.rounds):
        for persona_name in input.persona_list:
            persona = load_persona(persona_name)
            history = get_history(db, input.session_id)

            prompt = build_prompt(persona, history, current_message)
            bot_reply = query_llm(prompt)

            store_message(db, input.session_id, "bot", bot_reply)
            debate_history.append({"speaker": persona["name"], "text": bot_reply})

            current_message = bot_reply

    return {"transcript": debate_history}

# --- Message Endpoint ---
@app.post("/message/")
def send_message(input: MessageInput):
    db = next(get_db())

    session = db.query(Session).filter(Session.id == input.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    store_message(db, input.session_id, "user", input.user_message)

    persona = load_persona(input.persona_name)
    history = get_history(db, input.session_id)

    prompt = build_prompt(persona, history, input.user_message)
    bot_reply = query_llm(prompt)

    store_message(db, input.session_id, "bot", bot_reply)

    return {"prompt_used": prompt, "reply": bot_reply}

# --- Session Creation ---
@app.post("/start_session/")
def start_session():
    db = next(get_db())
    session = create_session(db)
    return {"session_id": session.id}

# --- Helpers ---
def create_session(db):
    session = Session()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def store_message(db, session_id: int, sender: str, content: str):
    msg = Message(session_id=session_id, sender=sender, content=content)
    db.add(msg)
    db.commit()
    return msg

def get_history(db, session_id: int, limit=10):
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).limit(limit).all()
    return [(m.sender, m.content) for m in msgs]

def load_persona(name):
    filename = os.path.join("personas", f"{name.lower()}.json")
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Persona '{name}' not found.")
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def build_prompt(persona, history, user_question):
    history_text = "\n".join([f"{sender}: {text}" for sender, text in history])

    beliefs = persona["beliefs"]
    beliefs_text = (
        f"- Political Beliefs: {beliefs['political']}\n"
        f"- Views on Freedom: {beliefs['freedom']}\n"
        f"- Views on War/Conflict: {beliefs['war']}\n"
        f"- Views on Government: {beliefs['government']}\n"
        f"- Key Values: {beliefs['values']}"
    )

    style = persona["style"]
    style_text = (
        f"Tone: {style['tone']}, Syntax: {style['syntax']}, "
        f"Common Phrases: {', '.join(style['phrases'])}, "
        f"Vocabulary Style: {style['vocab']}"
    )

    system_message = (
        f"You are {persona['name']}, a historical figure. "
        f"Speak in a way that matches your time period, beliefs, and personality.\n"
        f"Your core beliefs are:\n{beliefs_text}\n"
        f"Your speaking style is:\n{style_text}\n"
        f"Stay completely in character and do not break persona."
    )

    prompt = f"""{system_message}

Conversation so far:
{history_text}

User: {user_question}
{persona['name']}: """

    return prompt
