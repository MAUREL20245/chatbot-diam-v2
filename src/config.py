import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # Mode : "local" (Ollama) ou "cloud" (Groq)
    "mode": "cloud",

    # Modèle local (Ollama)
    "local_model": "llama3.2:3b",

    # Modèle cloud (Groq)
    "cloud_model": "mixtral-8x7b-32768",

    # Clé API Groq
    "groq_api_key": os.getenv("GROQ_API_KEY"),

    "temperature": 0.7,
    "embedding_model": "all-minilm",
    "chunk_size": 200,
    "chunk_overlap": 20,
    "k": 6,

    "system_prompt": """Tu es un assistant IA utile et concis. 
    Tu réponds toujours en français sauf si on te parle autrement."""
}

# Modèle actif selon le mode
CONFIG["model"] = CONFIG["cloud_model"] if CONFIG["mode"] == "cloud" else CONFIG["local_model"]