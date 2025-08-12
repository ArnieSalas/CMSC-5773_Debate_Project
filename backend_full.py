import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.middleware.cors import CORSMiddleware
import httpx

# ===============================
# Config: vLLM (OpenAI-compatible)
# ===============================
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "https://december-dx-mf-insulation.trycloudflare.com")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "sk-local")  # vLLM ignores it; some clients require a key
MODEL_ID = os.getenv("VLLM_MODEL", "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4")

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

# --- Pydantic models ---
class MessageInput(BaseModel):
    session_id: int
    user_message: str
    persona_name: str

class DebateInput(BaseModel):
    session_id: int
    starting_message: str
    persona_list: List[str]
    rounds: int = 3

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

def get_persona_history(db, session_id: int, persona_name: str, opponent_last: str) -> List[tuple]:
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    filtered = []
    if opponent_last:
        filtered.append(("user", opponent_last))  # treat opponent’s last as "user"
    persona_msgs = [m.content for m in msgs if m.sender == persona_name]
    for pm in persona_msgs[-2:]:  # last 2 persona messages
        filtered.append((persona_name, pm))
    return filtered

def truncate_message(message: str, max_tokens: int = 500) -> str:
    return message[:max_tokens]

def load_persona(name):
    filename = os.path.join("personas", f"{name.lower()}.json")
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Persona '{name}' not found.")
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def build_identity_messages(persona: Dict[str, Any]) -> List[Dict[str, str]]:
    beliefs = persona["beliefs"]
    tone = persona["style"]["tone"]

    # This merges and slightly harmonizes identity messages from both files
    return [
        {
            "role": "system",
            "content": (
                f"You are {persona['name']}, a historical figure. "
                "You are NOT an AI model and must never break character. "
                "Respond only as this figure, speaking in their authentic voice, values, and tone."
            )
        },
        {
            "role": "system",
            "content": (
                f"Character Profile:\n"
                f"Name: {persona['name']}\n"
                f"Tone: {tone}\n"
                f"Political Beliefs: {beliefs['political']}\n"
                f"Views on Freedom: {beliefs['freedom']}\n"
                f"Views on War: {beliefs['war']}\n"
                f"Views on Government: {beliefs['government']}\n"
                f"Core Values: {beliefs['values']}"
            )
        },
        {
            "role": "system",
            "content": (
                "Debate Guidelines:\n"
                "1. On your first turn, greet briefly and clearly state your stance.\n"
                "2. On later turns, avoid greetings and address your concerns and remarks.\n"
                "3. Never repeat your opener or use generic phrases like 'my fellow', 'audience', or 'folks' after the first two responses.\n"
                "4. Always address at least two specific points from your opponent's last statement.\n"
                "5. Add new reasoning or historical examples each turn.\n"
                "6. Keep responses under 6 sentences.\n"
                "7. Never contradict your declared stance.\n"
                "8. Remember who you are talking to."
            )
        }
    ]

def clean_user_message(message: str) -> str:
    unwanted_prefixes = ["Moderator:", "System:", "Instruction:"]
    for prefix in unwanted_prefixes:
        if message.startswith(prefix):
            message = message[len(prefix):].strip()
    return message

def build_chat_messages(persona: Dict[str, Any], history: List[tuple], user_question: str) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = []
    msgs.extend(build_identity_messages(persona))
    for sender, content in history:
        if sender == "user":
            msgs.append({"role": "user", "content": clean_user_message(content)})
        elif sender == "bot" or sender == persona["name"]:
            # accommodate both 'bot' and persona name as assistant
            msgs.append({"role": "assistant", "content": content})
    # Add system reminder at the end to reinforce persona
    msgs.append({
        "role": "system",
        "content": f"IMPORTANT: You are {persona['name']} only. Do not imitate other debaters."
    })
    # Current user input
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
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text
            print(f"vLLM Error: {detail}")
            raise HTTPException(status_code=502, detail=f"LLM error: {detail}")
        data = r.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Unexpected LLM Response: {data}")
            raise HTTPException(status_code=502, detail=f"Unexpected LLM response: {data}")

# --- API Endpoints ---

@app.post("/message/")
async def send_message(input: MessageInput):
    db = next(get_db())
    session = db.query(Session).filter(Session.id == input.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    user_message = truncate_message(input.user_message)
    store_message(db, input.session_id, "user", user_message)
    persona = load_persona(input.persona_name)
    history = get_history(db, input.session_id)
    messages = build_chat_messages(persona, history, user_message)
    bot_reply = await call_vllm_chat(messages, temperature=0.6, max_tokens=256)
    store_message(db, input.session_id, persona["name"], bot_reply)
    # Optional delay from first file (adjust as needed)
    await asyncio.sleep(1)
    return {"reply": bot_reply, "model": MODEL_ID, "session_id": input.session_id}

@app.post("/debate/")
async def start_debate(input: DebateInput, db=Depends(get_db)):
    session = db.query(Session).filter(Session.id == input.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if len(input.persona_list) < 2:
        raise HTTPException(status_code=400, detail="Need at least two personas.")
    debate_history = []
    opponent_last = input.starting_message
    for round_num in range(input.rounds):
        for persona_name in input.persona_list:
            persona = load_persona(persona_name)
            history = get_persona_history(db, input.session_id, persona_name, opponent_last)
            messages = build_chat_messages(persona, history, opponent_last)
            bot_reply = await call_vllm_chat(messages, temperature=0.6, max_tokens=256)
            store_message(db, input.session_id, persona["name"], bot_reply)
            debate_history.append({"speaker": persona_name, "text": bot_reply})
            opponent_last = bot_reply
    return {"transcript": debate_history}

@app.post("/start_session/")
def start_session():
    db = next(get_db())
    session = create_session(db)
    return {"session_id": session.id}

@app.get("/health")
async def health():
    # Check DB connectivity
    try:
        _ = next(get_db())
        db_ok = True
    except Exception:
        db_ok = False
    # Check vLLM server status
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{VLLM_BASE_URL}/health")
            vllm_ok = r.status_code == 200
            vllm_info = r.json() if vllm_ok else {"status": "down"}
    except Exception as e:
        vllm_ok = False
        vllm_info = {"error": str(e)}
    return {"db_ok": db_ok, "vllm_ok": vllm_ok, "vllm": vllm_info}
