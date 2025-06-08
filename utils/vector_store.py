import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from config import Config
import os

class VectorStoreManager:
    def __init__(self):
        self.config = Config()
        self.embeddings = self._get_embeddings()
        self.vector_store = self._initialize_vector_store()
    
    def _get_embeddings(self):
        if self.config.EMBEDDING_MODEL:
            return self.config.EMBEDDING_MODEL
        else:
            raise ValueError("Embedding model is not configured or their is some issue.")
    
    def _initialize_vector_store(self):
        os.makedirs(self.config.VECTOR_DB_PATH, exist_ok=True)
        
        # Create ChromaDB client with new configuration
        chroma_client = chromadb.PersistentClient(path=self.config.VECTOR_DB_PATH)
        
        return Chroma(
            client=chroma_client,
            collection_name="pdf_documents",
            embedding_function=self.embeddings,
        )
    
    def add_documents(self, documents, collection_name="pdf_documents"):
        """Add documents to vector store"""
        try:
            self.vector_store.add_documents(documents=documents)
            print(f"✅ Added {len(documents)} documents to vector store")
        except Exception as e:
            print(f"❌ Error adding documents: {str(e)}")
            raise e
    
    def similarity_search(self, query, k=5, collection_name="pdf_documents"):
        """Search for similar documents"""
        return self.vector_store.similarity_search(query, k=k)
    
    def get_retriever(self, k=5):
        """Get retriever for QA chain"""
        return self.vector_store.as_retriever(search_kwargs={"k": k})
    
