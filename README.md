# 🧠 Agent IA v2 — Club D.I.A.M

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Groq](https://img.shields.io/badge/Groq-Cloud%20LLM-orange)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-green)
![Redis](https://img.shields.io/badge/Redis-Mémoire%20Persistante-red)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)
![LangChain](https://img.shields.io/badge/LangChain-RAG-FFD700)
![Render](https://img.shields.io/badge/Render-Deployed-purple)

> Agent IA v2 construit progressivement dans le cadre du **Club D.I.A.M** —
> Version améliorée avec mémoire persistante Redis, lecture d'URLs et 6 outils intelligents.

🌍 **Demo Live** : [https://chatbot-diam-v2.onrender.com](https://chatbot-diam-v2.onrender.com)

---

## 🆕 Nouveautés v2 vs v1

| Fonctionnalité | v1 (chatbot-diam-cloud) | v2 (chatbot-diam-v2) |
|----------------|------------------------|----------------------|
| **Mémoire** | ❌ Oublie tout à chaque session | ✅ Redis persistant |
| **Lecture URLs** | ❌ Non disponible | ✅ Lit n'importe quelle page web |
| **Mémorisation** | ❌ Cherche dans les docs | ✅ Outil dédié `memoriser` |
| **Nombre d'outils** | 4 outils | 6 outils |
| **Session** | UUID aléatoire | ID stable via URL |

---

## 🎯 Vue d'ensemble

Ce projet est une plateforme IA modulaire et évolutive qui combine :

- 💬 **Chatbot conversationnel** basé sur un LLM (local ou cloud)
- 📚 **Système RAG** pour interroger vos propres documents (Pinecone)
- 🧠 **Mémoire persistante** entre les sessions (Redis Upstash)
- 🔗 **Lecture d'URLs** — lit et résume n'importe quelle page web
- ⚡ **API REST** exposant tous les services (FastAPI)
- 🧠 **Agent IA ReAct** capable de raisonner et d'utiliser des outils
- 🌐 **Recherche web** en temps réel (DuckDuckGo)
- 🐳 **Architecture Docker** pour un déploiement reproductible
- ☁️ **Déployé sur Render** avec Groq comme LLM cloud

---

## 🏗️ Architecture

```
chatbot-diam-v2/
├── src/
│   ├── config.py        # Configuration centralisée
│   ├── chatbot.py       # Logique du chatbot (Ollama local / Groq cloud)
│   ├── rag.py           # Système RAG (LangChain + Pinecone)
│   ├── agent.py         # Agent IA ReAct (from scratch) — 6 outils
│   └── memory.py        # Mémoire persistante (Redis Upstash) ← NOUVEAU
├── api/
│   ├── main.py          # Serveur FastAPI
│   └── routes/
│       ├── chat.py      # Endpoints /chat
│       └── rag.py       # Endpoints /rag
├── app.py               # Interface Streamlit — Chatbot
├── app_rag.py           # Interface Streamlit — RAG
├── app_agent.py         # Interface Streamlit — Agent v2 (déployé)
├── Dockerfile
├── docker-compose.yml
├── Procfile             # Configuration Render
└── requirements.txt
```

---

## 🚀 Stack Technologique

| Composant | Local | Cloud | Rôle |
|-----------|-------|-------|------|
| **LLM** | Ollama + llama3.2:3b | Groq + llama-3.3-70b | Génération de texte |
| **Embeddings** | all-minilm | multilingual-e5-large | Vectorisation |
| **Vector DB** | ChromaDB | Pinecone | Stockage des vecteurs |
| **Mémoire** | - | Redis (Upstash) | Historique persistant |
| **RAG** | LangChain | LangChain | Pipeline RAG |
| **Recherche web** | DuckDuckGo | DuckDuckGo | Infos en temps réel |
| **Lecture URLs** | WebBaseLoader | WebBaseLoader | Lire pages web |
| **API** | FastAPI + Uvicorn | FastAPI + Uvicorn | Exposition REST |
| **UI** | Streamlit | Streamlit | Interface utilisateur |
| **Agent** | ReAct (from scratch) | ReAct (from scratch) | Raisonnement + outils |
| **Deploy** | Docker Compose | Render | Orchestration |

---

## 🧠 Agent IA v2 — 6 Outils

```
Question → Thought → Action → Observation → Final Answer
```

| Outil | Capacité |
|-------|---------|
| 🧮 calculatrice | Calculs mathématiques |
| 🕐 date_heure | Date et heure actuelle |
| 💾 memoriser | Mémoriser infos personnelles (nom, projet...) |
| 🌐 recherche_web | Recherche internet (DuckDuckGo) |
| 📄 recherche_doc | Recherche dans les PDFs indexés (Pinecone) |
| 🔗 lire_url | Lire et résumer n'importe quelle page web |

---

## 💾 Mémoire persistante — Redis Upstash

```python
# src/memory.py
from upstash_redis import Redis

# Stockage de l'historique par session
add_message(session_id, "user", question)
add_message(session_id, "assistant", réponse)

# Récupération automatique à chaque message
history = format_history_for_prompt(session_id)
```

**Session stable via URL :**
```
https://chatbot-diam-v2.onrender.com?sid=abc12345
                                      ↑
                            ID unique par utilisateur
                            Mémoire retrouvée à chaque visite
```

---

## ⚙️ Configuration centralisée

```python
CONFIG = {
    "mode": "cloud",
    "local_model": "llama3.2:3b",
    "cloud_model": "llama-3.3-70b-versatile",
    "groq_api_key": os.getenv("GROQ_API_KEY"),
    "temperature": 0.7,
    "chunk_size": 700,
    "chunk_overlap": 100,
    "k": 10,
}
```

---

## 🐳 Démarrage local

```bash
git clone https://github.com/MAUREL20245/chatbot-diam-v2.git
cd chatbot-diam-v2
docker compose up -d
docker exec ollama ollama pull llama3.2:3b
```

---

## ☁️ Variables d'environnement Render

```
GROQ_API_KEY=votre_clé_groq
PINECONE_API_KEY=votre_clé_pinecone
UPSTASH_REDIS_REST_URL=votre_url_upstash
UPSTASH_REDIS_REST_TOKEN=votre_token_upstash
PYTHON_VERSION=3.11.9
```

---

## 📋 Roadmap

- [x] Phase 1 — Chatbot local (Ollama + Python)
- [x] Phase 2 — Interface Streamlit
- [x] Phase 3 — Système RAG (LangChain + ChromaDB)
- [x] Phase 4 — API REST (FastAPI)
- [x] Phase 5 — Agent IA (ReAct from scratch)
- [x] Phase 6 — Dockerisation (5 microservices)
- [x] Phase 7 — Déploiement Cloud (Groq + Pinecone + Render)
- [x] Phase 8 — Mémoire persistante (Redis Upstash) ← NOUVEAU
- [x] Phase 8 — Lecture d'URLs (WebBaseLoader) ← NOUVEAU
- [ ] Phase 9 — Envoi d'emails (Gmail API)
- [ ] Phase 10 — Agent autonome complet

---

## 👨‍💻 Auteur

**GUEPIE Aristide Maurel**  
Data Scientist / MLOps Engineer / AI Engineer  
📍 Abidjan, Côte d'Ivoire  
🔗 [Portfolio](https://maurel20245.github.io/chatbot-diam)  
🔗 [LinkedIn](https://www.linkedin.com/in/maurel-guepie-907b2b154/)

---

*"Ne pas juste suivre des tutoriels — comprendre l'architecture, construire progressivement, expérimenter, créer des solutions réelles."*  
**— Club D.I.A.M**