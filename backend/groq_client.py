# backend/groq_client.py
import requests
from backend.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
    "Content-Type": "application/json",
}

def ask_groq(user_message: str, history: list | None = None, system_prompt: str | None = None) -> str:
    if history is None:
        history = []
    messages = []
    messages.append({"role": "system", "content": system_prompt or "You are John — a professional customer support AI."})
    for h in history:
        # expect dicts with {"role":"user"/"assistant", "content":"..."}
        messages.append(h)
    messages.append({"role":"user", "content": user_message})

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 800,
    }
    r = requests.post(GROQ_URL, headers=HEADERS, json=payload, timeout=30)
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Groq responded non-json ({r.status_code})")
    if r.status_code != 200:
        # propagate helpful error
        raise RuntimeError(f"Groq error: {data.get('error') if isinstance(data, dict) else r.text}")
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError("Unexpected Groq response shape: " + str(e))

