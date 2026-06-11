from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_pinecone import PineconeVectorStore
from langchain_core.embeddings import Embeddings
from groq import Groq
from pinecone import Pinecone
from src.config import CONFIG
import os

INDEX_NAME = "chatbot-diam"


class PineconeInferenceEmbeddings(Embeddings):
    """Embeddings via l'API d'inférence Pinecone — pas de modèle local"""

    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.model = "multilingual-e5-large"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result = self.pc.inference.embed(
            model=self.model,
            inputs=texts,
            parameters={"input_type": "passage"}
        )
        return [item["values"] for item in result]

    def embed_query(self, text: str) -> list[float]:
        result = self.pc.inference.embed(
            model=self.model,
            inputs=[text],
            parameters={"input_type": "query"}
        )
        return result[0]["values"]


class RAGSystem:
    def __init__(self):
        self.embeddings = PineconeInferenceEmbeddings()
        self.groq_client = Groq(api_key=CONFIG["groq_api_key"])
        self.vectorstore = None
        self._init_pinecone()

    def _init_pinecone(self):
        try:
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            index = pc.Index(INDEX_NAME)
            self.vectorstore = PineconeVectorStore(
                index=index,
                embedding=self.embeddings,
                text_key="text"
            )
        except Exception as e:
            print(f"Pinecone init error: {e}")

    def load_document(self, file_path: str) -> list:
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError("Format non supporté.")
        return loader.load()

    def index_document(self, file_path: str, original_name: str = None) -> int:
        documents = self.load_document(file_path)
        if original_name:
            for doc in documents:
                doc.metadata["source"] = original_name
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG["chunk_size"],
            chunk_overlap=CONFIG["chunk_overlap"]
        )
        chunks = splitter.split_documents(documents)
        self.vectorstore = PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            index_name=INDEX_NAME
        )
        return len(chunks)

    def ask(self, question: str) -> dict:
        if self.vectorstore is None:
            return {"answer": "Aucun document indexé.", "sources": []}

        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": CONFIG["k"]}
        )
        source_docs = retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in source_docs)

        response = self.groq_client.chat.completions.create(
            model=CONFIG["model"],
            messages=[
                {"role": "system", "content": """Tu es un assistant expert en analyse de documents.
Réponds de manière PRÉCISE et DÉTAILLÉE en te basant UNIQUEMENT sur le contexte fourni.

RÈGLES STRICTES :
- Cite les informations EXACTES du document — pas de paraphrase vague
- Utilise les termes précis du document
- Ne dis JAMAIS "semble être" ou "pourrait être" — sois affirmatif
- Si l'info n'est pas dans le contexte → dis clairement "Je ne trouve pas cette information dans vos documents"
- Ne réponds JAMAIS depuis ta connaissance générale
- Structure ta réponse avec des points clairs si nécessaire"""},
                {"role": "user", "content": f"Contexte extrait du document :\n{context}\n\nQuestion : {question}\n\nRéponds de manière précise et détaillée en te basant uniquement sur le contexte ci-dessus."}
            ]
        )

        answer = response.choices[0].message.content
        sources = list(set([
            os.path.basename(doc.metadata.get("source", "inconnu"))
            for doc in source_docs
        ]))

        return {"answer": answer, "sources": sources}

    def reset(self):
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)
        index.delete(delete_all=True)
        self.vectorstore = None