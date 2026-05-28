from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from groq import Groq
from src.config import CONFIG
import os

INDEX_NAME = "chatbot-diam"


class RAGSystem:
    def __init__(self, model: str = CONFIG["model"]):
        self.model = model

        # Embeddings via HuggingFace (sentence-transformers)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        # Client Groq pour la génération
        self.groq_client = Groq(api_key=CONFIG["groq_api_key"])

        # Pinecone vectorstore
        self.vectorstore = None
        self._init_pinecone()

    def _init_pinecone(self):
        """Initialiser la connexion Pinecone"""
        try:
            from pinecone import Pinecone
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

    def index_document(self, file_path: str) -> int:
        documents = self.load_document(file_path)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG["chunk_size"],
            chunk_overlap=CONFIG["chunk_overlap"]
        )
        chunks = splitter.split_documents(documents)

        # Indexer dans Pinecone
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)

        self.vectorstore = PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            index_name=INDEX_NAME
        )

        return len(chunks)

    def ask(self, question: str) -> dict:
        if self.vectorstore is None:
            return {
                "answer": "Aucun document indexé.",
                "sources": []
            }

        # Récupérer les chunks similaires
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": CONFIG["k"]}
        )
        source_docs = retriever.invoke(question)

        # Construire le contexte
        context = "\n\n".join(doc.page_content for doc in source_docs)

        # Générer la réponse via Groq
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Tu réponds aux questions en te basant uniquement sur le contexte fourni. Si la réponse n'est pas dans le contexte, dis-le clairement."
                },
                {
                    "role": "user",
                    "content": f"Contexte:\n{context}\n\nQuestion: {question}"
                }
            ]
        )

        answer = response.choices[0].message.content

        sources = []
        for doc in source_docs:
            source = doc.metadata.get("source", "inconnu")
            page = doc.metadata.get("page", "")
            sources.append(
                f"{os.path.basename(source)}" +
                (f" (page {page+1})" if page != "" else "")
            )

        return {
            "answer": answer,
            "sources": list(set(sources))
        }

    def reset(self):
        """Vider l'index Pinecone"""
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)
        index.delete(delete_all=True)
        self.vectorstore = None