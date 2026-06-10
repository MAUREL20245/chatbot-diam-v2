import streamlit as st
from src.agent import AIAgent
import tempfile
import os

# ── Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Agent IA — Club D.I.A.M",
    page_icon="🤖",
    layout="centered"
)

st.title("🧠 Agent IA — Club D.I.A.M")
st.caption("Un agent capable de raisonner et d'utiliser des outils — Propulsé par Groq")

# ── Initialisation ────────────────────────────────────────────────
if "agent" not in st.session_state:
    with st.spinner("Initialisation de l'agent..."):
        st.session_state.agent = AIAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Outils disponibles")
    st.markdown("""
    | Outil | Rôle |
    |-------|------|
    | 🧮 calculatrice | Calculs mathématiques |
    | 🕐 date_heure | Date et heure actuelle |
    | 🌐 recherche_web | Chercher sur internet |
    | 📄 recherche_doc | Chercher dans les PDFs |
    """)

    st.divider()
    st.markdown("**Exemples de questions :**")
    st.markdown("""
    - *Quelle heure est-il ?*
    - *Calcule 15% de 85000*
    - *Quelles sont les dernières nouvelles IA ?*
    - *Quels sont les modules B2 dans mes documents ?*
    """)

    st.divider()
    st.header("📂 Mes Documents")

    uploaded_file = st.file_uploader(
        "Charge un document",
        type=["pdf", "txt"],
        help="PDF ou TXT uniquement"
    )

    if uploaded_file is not None:
        if uploaded_file.name not in st.session_state.indexed_files:
            with st.spinner(f"Indexation de {uploaded_file.name}..."):
                from src.rag import RAGSystem
                rag = RAGSystem()
                suffix = ".pdf" if uploaded_file.name.endswith(".pdf") else ".txt"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                # ── Fix : passer le vrai nom du fichier ──
                nb_chunks = rag.index_document(tmp_path, original_name=uploaded_file.name)
                os.unlink(tmp_path)
                st.session_state.indexed_files.append(uploaded_file.name)
            st.success(f"✅ {uploaded_file.name} indexé ({nb_chunks} chunks)")

    if st.session_state.indexed_files:
        st.subheader("Documents indexés :")
        for f in st.session_state.indexed_files:
            st.markdown(f"📄 {f}")

    st.divider()
    # ── Fix : bouton Effacer complet ──
    if st.button("🗑️ Effacer", use_container_width=True):
        st.session_state.messages = []
        st.session_state.indexed_files = []
        st.rerun()

# ── Historique ────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Saisie ────────────────────────────────────────────────────────
if prompt := st.chat_input("Pose une question à l'agent..."):

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("assistant"):
        with st.spinner("L'agent réfléchit et agit..."):
            response = st.session_state.agent.run(prompt)

        if "Final Answer:" in response:
            clean_response = response.split("Final Answer:")[-1].strip()
        else:
            clean_response = response

        st.markdown(clean_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": clean_response
    })