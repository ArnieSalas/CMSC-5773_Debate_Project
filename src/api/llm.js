const BASE = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function startSession() {
  const r = await fetch(`${BASE}/start_session/`, { method: "POST" });
  if (!r.ok) throw new Error("Failed to start session");
  const { session_id } = await r.json();
  return session_id;
}

export async function sendMessage({ session_id, user_message, persona_name }) {
  const r = await fetch(`${BASE}/message/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, user_message, persona_name }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`LLM error: ${text}`);
  }
  return await r.json(); // { reply, model, session_id }
}
