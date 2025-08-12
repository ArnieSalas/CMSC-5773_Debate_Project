import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import httpx
from typing import List, Dict, Any

# ===============================
# Config: vLLM (OpenAI-compatible)
# ===============================
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "https://december-dx-mf-insulation.trycloudflare.com")  # <-- set your tunnel URL here or via env
VLLM_API_KEY  = os.getenv("VLLM_API_KEY", "sk-local")  # vLLM ignores it; some clients require a key
MODEL_ID      = os.getenv("VLLM_MODEL", "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4")

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
    allow_origins=["*"],  #Restrict to ["http://localhost:5173"] if preferred
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic models ---
class MessageInput(BaseModel):
    session_id: int
    user_message: str
    persona_name: str

# --- Utility functions ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

def get_history(db, session_id: int, limit=5):
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).limit(limit).all()
    return [(m.sender, m.content) for m in msgs]

def truncate_message(message: str, max_tokens: int = 500) -> str:
    return message[:max_tokens]

def load_persona(name):
    filename = os.path.join("personas", f"{name.lower()}.json")
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Persona '{name}' not found.")
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def build_identity_messages(persona: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return multiple system messages to lock in the role/persona."""
    beliefs = persona["beliefs"]
    tone = persona["style"]["tone"]

    return [
        {
            "role": "system",
            "content": (
                f"You are roleplaying as {persona['name']}, a historical figure. "
                "You are NOT an AI model. You are {persona['name']} and will never break character. "
                "You respond ONLY as this figure, speaking in their voice, values, and tone. "
                "Do not ever acknowledge or refer to yourself as an AI or anything other than the character you are portraying."
            )
        },
        {
            "role": "system",
            "content": (
                f"Character Sheet:\n"
                f"Name: {persona['name']}\n"
                f"Tone: {tone}\n"
                f"Core Beliefs:\n"
                f"- Political: {beliefs['political']}\n"
                f"- Freedom: {beliefs['freedom']}\n"
                f"- War: {beliefs['war']}\n"
                f"- Government: {beliefs['government']}\n"
                f"- Values: {beliefs['values']}"
            )
        },
        {
            "role": "system",
            "content": (
                "Debate Rules:\n"
                "1. Speak in 7 sentences or less.\n"
                "2. Always address the audience as 'audience'.\n"
                "3. If asked about modern topics, respond as this historical figure would have, "
                "based on their values and worldview. Never break character and always stay true to the historical persona."
            )
        }
    ]

def clean_user_message(message: str) -> str:
    """Remove meta/moderator phrasing from the user message."""
    # Simple example — you could make this smarter
    unwanted_prefixes = ["Moderator:", "System:", "Instruction:"]
    for prefix in unwanted_prefixes:
        if message.startswith(prefix):
            message = message[len(prefix):].strip()
    return message

def build_chat_messages(persona: Dict[str, Any], history: List[tuple], user_question: str) -> List[Dict[str, str]]:
    """Convert DB history to OpenAI-style chat messages while keeping persona consistent."""
    msgs: List[Dict[str, str]] = []

    # Add multi-part system setup
    msgs.extend(build_identity_messages(persona))

    # Replay only dialogue history (no system/meta)
    for sender, content in history:
        if sender == "user":
            msgs.append({"role": "user", "content": clean_user_message(content)})
        elif sender == "bot":
            msgs.append({"role": "assistant", "content": content})

    # Add short identity reminder before latest user message
    msgs.append({
        "role": "system",
        "content": f"Reminder: You are {persona['name']}, speaking only in their historical voice."
    })

    # Add current user input (cleaned)
    msgs.append({"role": "user", "content": clean_user_message(user_question)})

    return msgs

async def call_vllm_chat(messages: List[Dict[str, str]], temperature: float = 0.6, max_tokens: int = 512) -> str:
    url = f"{VLLM_BASE_URL}/v1/chat/completions"
    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {VLLM_API_KEY}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(60.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, headers=headers, json=payload)
        try:
            r.raise_for_status()  # Raise HTTPError for bad responses
        except httpx.HTTPStatusError as e:
            # Log response content for debugging
            detail = e.response.text
            print(f"vLLM Error: {detail}")  # Log the exact response
            raise HTTPException(status_code=502, detail=f"LLM error: {detail}")

        data = r.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Unexpected LLM Response: {data}")  # Log unexpected data
            raise HTTPException(status_code=502, detail=f"Unexpected LLM response: {data}")


# --- API Endpoints ---
@app.post("/message/")

async def send_message(input: MessageInput):
    db = next(get_db())

    # Validate session
    session = db.query(Session).filter(Session.id == input.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Store user message
    user_message = truncate_message(input.user_message)  # Truncate the user message
    store_message(db, input.session_id, "user", user_message)

    # Load persona and conversation history
    persona = load_persona(input.persona_name)
    history = get_history(db, input.session_id)

    # Build chat messages for the model
    messages = build_chat_messages(persona, history, user_message)

    # Call the model with reduced max_tokens
    bot_reply = await call_vllm_chat(messages, temperature=0.6, max_tokens=256)  # Reduced max_tokens

    # Store bot message
    store_message(db, input.session_id, "bot", bot_reply)

    # Delay for next bot responses
    await asyncio.sleep(10)  # 1 second delay

    return {
        "reply": bot_reply,
        "model": MODEL_ID,
        "session_id": input.session_id,
    }

@app.post("/start_session/")
def start_session():
    db = next(get_db())
    session = create_session(db)
    return {"session_id": session.id}

@app.get("/health")
async def health():
    """Check DB and vLLM health."""
    # DB ping
    try:
        _ = next(get_db())
        db_ok = True
    except Exception:
        db_ok = False

    # vLLM ping
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{VLLM_BASE_URL}/health")
            vllm_ok = r.status_code == 200
            vllm_info = r.json() if vllm_ok else {"status": "down"}
    except Exception as e:
        vllm_ok = False
        vllm_info = {"error": str(e)}

    return {"db_ok": db_ok, "vllm_ok": vllm_ok, "vllm": vllm_info}