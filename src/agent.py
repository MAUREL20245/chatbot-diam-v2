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

def recherche_doc(question: str) -> str:
    rag = get_rag()
    result = rag.ask(question)
    answer = result["answer"]
    sources = result.get("sources", [])
    if sources:
        answer += f"\n\n📎 Source : {', '.join(sources)}"
    return answer

search = DuckDuckGoSearchRun()

TOOLS = {
    "calculatrice": calculatrice,
    "date_heure": date_heure,
    "recherche_web": search.run,
    "recherche_doc": recherche_doc,
}

TOOLS_DESCRIPTION = """
- calculatrice : faire des calculs. Ex: '2 + 2', 'sqrt(16)', '15 * 85000 / 100'
- date_heure : connaître la date et l'heure actuelle
- recherche_web : chercher des infos récentes sur internet
- recherche_doc : chercher dans les documents PDF indexés
"""

REACT_PROMPT = """Tu es un assistant IA. Tu DOIS obligatoirement utiliser un outil avant de répondre.
Tu réponds TOUJOURS en français.

{history}

Outils disponibles :
{tools}

RÈGLE ABSOLUE : Tu ne peux JAMAIS répondre directement sans passer par un outil.
Même si tu penses connaître la réponse, tu DOIS utiliser l'outil correspondant.

Format OBLIGATOIRE à respecter :

Thought: réfléchis à quel outil utiliser
Action: nom_exact_de_l_outil
Action Input: ce que tu passes à l_outil
Observation: [le système mettra le résultat ici]
Thought: j'ai le résultat
Final Answer: ta réponse en français

IMPORTANT :
- Pour l'heure ou la date → utilise OBLIGATOIREMENT date_heure
- Pour un calcul → utilise OBLIGATOIREMENT calculatrice
- Pour une actualité → utilise OBLIGATOIREMENT recherche_web
- Pour les documents → utilise OBLIGATOIREMENT recherche_doc avec LA QUESTION EXACTE de l'utilisateur comme Action Input
- Si la question fait référence à la conversation précédente → utilise l'historique fourni

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

        # Récupérer l'historique
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
                # Sauvegarder dans la mémoire
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

                if tool_name == "recherche_doc":
                    source_lines = [l for l in observation.split("\n") if "📎 Source" in l]
                    if source_lines and "📎 Source" not in final:
                        final += "\n\n" + source_lines[0]

                # Sauvegarder dans la mémoire
                add_message(session_id, "user", question)
                add_message(session_id, "assistant", final)
                return final
            else:
                return response

        return "Je n'ai pas pu trouver une réponse après 5 tentatives."