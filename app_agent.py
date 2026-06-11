import streamlit as st
from src.agent import AIAgent
import tempfile
import os
import uuid

# ── Configuration ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Agent AYNID",
    page_icon="🤖",
    layout="wide"
)

# ── Thème WhatsApp ─────────────────────────────────────────────────
st.markdown("""
<style>

/* Fond général blanc */
.stApp {
    background-color: #FFFFFF;
}

/* Sidebar fond blanc, bordure verte */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 3px solid #25D366;
}

/* Texte sidebar VISIBLE en noir */
[data-testid="stSidebar"] * {
    color: #111B21 !important;
}

/* Barre du bas — propre, fond blanc */
.stBottom {
    bottom: 20px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 70% !important;
    border-radius: 35px !important;
    box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3) !important;
}

.stBottom, .stBottom > div, .stBottom > div > div {
    background-color: #FFFFFF !important;
    border: 2px solid #25D366 !important;
    border-radius: 35px !important;
}

/* Espace suffisant pour que le chat ne se cache pas */
.main .block-container {
    padding-bottom: 120px !important;
}

/* Container du champ de saisie */
[data-testid="stChatInput"] {
    background-color: #FFFFFF !important;
    border-radius: 30px !important;
}

/* Champ de saisie */
[data-testid="stChatInput"] textarea {
    background-color: #F0FFF4 !important;
    color: #111B21 !important;
    border: 2px solid #25D366 !important;
    border-radius: 25px !important;
    min-height: 50px !important;
    padding: 12px 20px !important;
    font-size: 15px !important;
}

/* Bouton envoi vert */
[data-testid="stChatInputSubmitButton"] {
    background-color: #25D366 !important;
    border-radius: 50% !important;
}

/* Titres en vert + plus grand */
h1 {
    color: #128C7E !important;
    font-size: 3rem !important;
    font-weight: 700 !important;
}

h2, h3 {
    color: #128C7E !important;
}

/* Zone chat fond légèrement vert clair */
[data-testid="stChatMessageContainer"] {
    background-color: #F9FFF9;
}

/* Texte des messages visible en noir */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span {
    color: #111B21 !important;
}

/* Bulle utilisateur — vert clair */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background-color: #DCF8C6 !important;
    border-radius: 12px !important;
    padding: 10px 16px !important;
}

/* Bulle agent — blanc avec bordure verte */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background-color: #FFFFFF !important;
    border: 1px solid #25D366 !important;
    border-radius: 12px !important;
    padding: 10px 16px !important;
}

/* Zone upload - fond vert clair avec bordure verte pointillée */
[data-testid="stFileUploader"] {
    background-color: #F0FFF4 !important;
    border: 2px dashed #25D366 !important;
    border-radius: 12px !important;
    padding: 10px !important;
}

/* Texte dans la zone upload */
[data-testid="stFileUploader"] * {
    color: #128C7E !important;
}

/* Bouton Télécharger en vert */
[data-testid="stFileUploader"] button {
    background-color: #25D366 !important;
    color: white !important;
    border: none !important;
    border-radius: 20px !important;
}

/* Bouton Effacer en vert */
[data-testid="stSidebar"] .stButton button {
    background-color: #25D366 !important;
    color: white !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: bold !important;
}

/* Hover bouton */
[data-testid="stSidebar"] .stButton button:hover {
    background-color: #128C7E !important;
}

</style>
""", unsafe_allow_html=True)

st.title("🧠 Agent AYNID")
st.caption("Agent avec mémoire persistante — Propulsé par Groq + Redis")

# ── Initialisation ────────────────────────────────────────────────
if "agent" not in st.session_state:
    with st.spinner("Initialisation de l'agent..."):
        st.session_state.agent = AIAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

if "session_id" not in st.session_state:
    session_id = st.query_params.get("sid", None)
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
        st.query_params["sid"] = session_id
    st.session_state.session_id = session_id

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
    | 🔗 lire_url | Lire une page web |
    """)

    st.divider()
    st.markdown("**Exemples de questions :**")
    st.markdown("""
    - *Quelle heure est-il ?*
    - *Calcule 15% de 85000*
    - *Quelles sont les dernières nouvelles IA ?*
    - *Lis cette page : https://...*
    - *Comment je m'appelle ?*
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
                nb_chunks = rag.index_document(tmp_path, original_name=uploaded_file.name)
                os.unlink(tmp_path)
                st.session_state.indexed_files.append(uploaded_file.name)
            st.success(f"✅ {uploaded_file.name} indexé ({nb_chunks} chunks)")

    if st.session_state.indexed_files:
        st.subheader("Documents indexés :")
        for f in st.session_state.indexed_files:
            st.markdown(f"📄 {f}")

    st.divider()
    if st.button("🗑️ Effacer", use_container_width=True):
        from src.memory import clear_history
        clear_history(st.session_state.session_id)
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
            response = st.session_state.agent.run(
                prompt,
                session_id=st.session_state.session_id
            )

        if "Final Answer:" in response:
            clean_response = response.split("Final Answer:")[-1].strip()
        else:
            clean_response = response

        st.markdown(clean_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": clean_response
    })