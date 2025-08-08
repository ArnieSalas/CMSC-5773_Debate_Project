from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import json
import os

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
    history_text = "\n".join([f"{sender.capitalize()}: {text}" for sender, text in history])
    
    # Combine beliefs for the prompt
    beliefs = persona["beliefs"]
    beliefs_text = "\n- Political: " + beliefs["political"]
    beliefs_text += "\n- Freedom: " + beliefs["freedom"]
    beliefs_text += "\n- War: " + beliefs["war"]
    beliefs_text += "\n- Government: " + beliefs["government"]
    beliefs_text += "\n- Values: " + beliefs["values"]

    prompt = f"""You are {persona['name']}, a historical figure.
Your tone is: {persona['style']['tone']}
Your core beliefs are:{beliefs_text}

Conversation history:
{history_text}

User: {user_question}
{persona['name']}: """
    
    return prompt

# --- API Endpoints ---
@app.post("/message/")
def send_message(input: MessageInput):
    db = next(get_db())

    # Validate session
    session = db.query(Session).filter(Session.id == input.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Store user message
    store_message(db, input.session_id, "user", input.user_message)

    # Load persona and conversation history
    persona = load_persona(input.persona_name)
    history = get_history(db, input.session_id)

    # Build prompt (use your LLM here instead of dummy reply)
    prompt = build_prompt(persona, history, input.user_message)

    # Dummy bot reply (replace with model call)
    bot_reply = f"(Pretend I am {persona['name']}) That's a profound question."
    store_message(db, input.session_id, "bot", bot_reply)

    return {"prompt_used": prompt, "reply": bot_reply}

@app.post("/start_session/")
def start_session():
    db = next(get_db())
    session = create_session(db)
    return {"session_id": session.id}
