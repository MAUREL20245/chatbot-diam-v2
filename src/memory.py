from upstash_redis import Redis
import os
import json

# ── Connexion Redis Upstash ───────────────────────────────────────
redis_client = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
)

MAX_HISTORY = 10  # Nombre max de messages à garder en mémoire

def get_history(session_id: str) -> list:
    """Récupère l'historique de conversation"""
    try:
        data = redis_client.get(f"history:{session_id}")
        if data:
            return json.loads(data)
        return []
    except Exception as e:
        print(f"Redis get error: {e}")
        return []

def save_history(session_id: str, history: list):
    """Sauvegarde l'historique de conversation"""
    try:
        # Garder seulement les MAX_HISTORY derniers messages
        if len(history) > MAX_HISTORY * 2:
            history = history[-(MAX_HISTORY * 2):]
        redis_client.set(
            f"history:{session_id}",
            json.dumps(history),
            ex=86400  # Expire après 24h
        )
    except Exception as e:
        print(f"Redis save error: {e}")

def add_message(session_id: str, role: str, content: str):
    """Ajoute un message à l'historique"""
    history = get_history(session_id)
    history.append({"role": role, "content": content})
    save_history(session_id, history)

def clear_history(session_id: str):
    """Efface l'historique de conversation"""
    try:
        redis_client.delete(f"history:{session_id}")
    except Exception as e:
        print(f"Redis delete error: {e}")

def format_history_for_prompt(session_id: str) -> str:
    """Formate l'historique pour l'injecter dans le prompt"""
    history = get_history(session_id)
    if not history:
        return ""
    
    formatted = "\n=== Historique de la conversation ===\n"
    for msg in history:
        role = "Utilisateur" if msg["role"] == "user" else "Assistant"
        formatted += f"{role}: {msg['content']}\n"
    formatted += "=====================================\n"
    return formatted