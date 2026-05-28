import streamlit as st
from src.rag import RAGSystem
import tempfile
import os

# ── Configuration de la page ──────────────────────────────────────
st.set_page_config(
    page_title="Chatbot RAG — Club D.I.A.M",
    page_icon="📚",
    layout="centered"
)

st.title(" Chatbot RAG — Club D.I.A.M")
st.caption("Pose des questions sur vos propres documents — Propulsé par Groq + Pinecone")

# ── Initialisation ────────────────────────────────────────────────
if "rag" not in st.session_state:
    st.session_state.rag = RAGSystem()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

# ── Sidebar : Upload et contrôles ────────────────────────────────
with st.sidebar:
    st.header("📂 Mes Documents")

    uploaded_file = st.file_uploader(
        "Charge un document",
        type=["pdf", "txt"],
        help="PDF ou TXT uniquement"
    )

    if uploaded_file is not None:
        if uploaded_file.name not in st.session_state.indexed_files:
            with st.spinner(f"Indexation de {uploaded_file.name}..."):
                # Sauvegarder temporairement le fichier
                suffix = ".pdf" if uploaded_file.name.endswith(".pdf") else ".txt"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                # Indexer le document
                nb_chunks = st.session_state.rag.index_document(tmp_path)
                os.unlink(tmp_path)  # Supprimer le fichier temporaire

                st.session_state.indexed_files.append(uploaded_file.name)

            st.success(f"{uploaded_file.name} indexé ({nb_chunks} chunks)")

    # Liste des documents indexés
    if st.session_state.indexed_files:
        st.subheader("Documents indexés :")
        for f in st.session_state.indexed_files:
            st.markdown(f"📄 {f}")

    st.divider()

    # Bouton reset
    if st.button("🗑️ Tout effacer", use_container_width=True):
        st.session_state.rag.reset()
        st.session_state.messages = []
        st.session_state.indexed_files = []
        st.rerun()

# ── Affichage de l'historique ─────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📎 Sources utilisées"):
                for source in message["sources"]:
                    st.markdown(f"- {source}")

# ── Zone de saisie ────────────────────────────────────────────────
if prompt := st.chat_input("Pose une question sur tes documents..."):

    # Afficher le message utilisateur
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Obtenir la réponse RAG
    with st.chat_message("assistant"):
        with st.spinner("Recherche dans les documents..."):
            result = st.session_state.rag.ask(prompt)

        st.markdown(result["answer"])

        if result["sources"]:
            with st.expander("📎 Sources utilisées"):
                for source in result["sources"]:
                    st.markdown(f"- {source}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })