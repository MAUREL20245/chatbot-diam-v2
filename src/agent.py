from groq import Groq
from langchain_community.tools import DuckDuckGoSearchRun
from src.config import CONFIG
from src.rag import RAGSystem
from datetime import datetime
import math
import re

# ── Instance RAG unique ───────────────────────────────────────────
_rag_instance = None

def get_rag() -> RAGSystem:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
    return _rag_instance

# ── Outils ───────────────────────────────────────────────────────

def calculatrice(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return f"Résultat : {result}"
    except Exception as e:
        return f"Erreur : {str(e)}"

def date_heure(query: str) -> str:
    now = datetime.now()
    return f"Nous sommes le {now.strftime('%A %d %B %Y')} à {now.strftime('%H:%M')}"

def memoriser(info: str) -> str:
    """Mémorise une information personnelle sur l'utilisateur"""
    return f"✅ Information mémorisée : {info}"

def recherche_doc(question: str) -> str:
    rag = get_rag()
    result = rag.ask(question)
    answer = result["answer"]
    sources = result.get("sources", [])
    if sources:
        answer += f"\n\n📎 Source : {', '.join(sources)}"
    return answer

def lire_url(url: str) -> str:
    try:
        from langchain_community.document_loaders import WebBaseLoader
        loader = WebBaseLoader(url)
        docs = loader.load()
        if not docs:
            return "Impossible de lire cette URL."
        contenu = docs[0].page_content[:3000]
        return f"Contenu de {url} :\n\n{contenu}"
    except Exception as e:
        return f"Erreur lors de la lecture de l'URL : {str(e)}"

search = DuckDuckGoSearchRun()

TOOLS = {
    "calculatrice": calculatrice,
    "date_heure": date_heure,
    "memoriser": memoriser,
    "recherche_web": search.run,
    "recherche_doc": recherche_doc,
    "lire_url": lire_url,
}

TOOLS_DESCRIPTION = """
- calculatrice : faire des calculs. Ex: '2 + 2', 'sqrt(16)', '15 * 85000 / 100'
- date_heure : connaître la date et l'heure actuelle
- memoriser : mémoriser une info personnelle sur l'utilisateur. Ex: nom, prénom, entreprise, projet
- recherche_web : chercher des infos récentes sur internet
- recherche_doc : chercher dans les documents PDF indexés
- lire_url : lire et résumer le contenu d'une page web. Ex: 'https://example.com'
"""

REACT_PROMPT = """Tu es un assistant IA intelligent et précis.
Tu réponds TOUJOURS en français.

{history}

Outils disponibles :
{tools}

RÈGLE ABSOLUE : Tu DOIS obligatoirement utiliser un outil avant de répondre.

Format OBLIGATOIRE à respecter :

Thought: réfléchis à quel outil utiliser
Action: nom_exact_de_l_outil
Action Input: ce que tu passes à l_outil
Observation: [le système mettra le résultat ici]
Thought: j'ai le résultat
Final Answer: ta réponse en français

IMPORTANT — Choix de l'outil :
- "Je m'appelle X" / "Mon nom est X" / info personnelle → utilise OBLIGATOIREMENT memoriser
- Question sur l'utilisateur (nom, entreprise...) → vérifie D'ABORD l'historique, réponds directement
- Pour l'heure ou la date → utilise OBLIGATOIREMENT date_heure
- Pour un calcul → utilise OBLIGATOIREMENT calculatrice
- Pour une actualité/news → utilise OBLIGATOIREMENT recherche_web
- Pour les documents PDF → utilise OBLIGATOIREMENT recherche_doc avec LA QUESTION EXACTE
- Pour lire une URL → utilise OBLIGATOIREMENT lire_url avec l'URL exacte

Question : {question}
"""

class AIAgent:
    def __init__(self):
        self.client = Groq(api_key=CONFIG["groq_api_key"])
        self.model = CONFIG["model"]

    def _call_llm(self, prompt: str, stop: list = None) -> str:
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        if stop:
            kwargs["stop"] = stop
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def run(self, question: str, session_id: str = "default") -> str:
        from src.memory import format_history_for_prompt, add_message

        history = format_history_for_prompt(session_id)

        prompt = REACT_PROMPT.format(
            tools=TOOLS_DESCRIPTION,
            history=history,
            question=question
        )

        for i in range(5):
            response = self._call_llm(prompt, stop=["Observation:"])
            print(f"\n--- Itération {i+1} ---\n{response}")

            if "Final Answer:" in response:
                final = response.split("Final Answer:")[-1].strip()
                # Supprimer source si réponse depuis mémoire
                if "📎 Source" in final:
                    final = final.split("📎 Source")[0].strip()
                add_message(session_id, "user", question)
                add_message(session_id, "assistant", final)
                return final

            action_match = re.search(r"Action:\s*(\w+)", response)
            input_match = re.search(r"Action Input:\s*(.+)", response)

            if action_match and input_match:
                tool_name = action_match.group(1).strip()
                tool_input = input_match.group(1).strip().strip("'\"")

                if not tool_input or "None" in tool_input or "je vais" in tool_input.lower():
                    tool_input = question

                if tool_name == "recherche_doc":
                    tool_input = question

                if tool_name in TOOLS:
                    observation = TOOLS[tool_name](tool_input)
                else:
                    observation = f"Outil '{tool_name}' inconnu."

                print(f"Outil : {tool_name} | Input : {tool_input}")
                print(f"Observation : {observation}")

                prompt += f"\n{response}\nObservation: {observation}\nThought: J'ai le résultat, je formule la réponse finale.\nFinal Answer:"
                final = self._call_llm(prompt)
                final = final.strip()

                # Source uniquement pour recherche_doc
                if tool_name == "recherche_doc":
                    source_lines = [l for l in observation.split("\n") if "📎 Source" in l]
                    if source_lines and "📎 Source" not in final:
                        final += "\n\n" + source_lines[0]

                # Pas de source pour memoriser et autres outils
                if tool_name in ["memoriser", "date_heure", "calculatrice", "recherche_web", "lire_url"]:
                    if "📎 Source" in final:
                        final = final.split("📎 Source")[0].strip()

                add_message(session_id, "user", question)
                add_message(session_id, "assistant", final)
                return final
            else:
                return response

        return "Je n'ai pas pu trouver une réponse après 5 tentatives."