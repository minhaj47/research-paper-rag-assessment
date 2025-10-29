from typing import List
from .document_processor import DocumentProcessor
from .embedding_service import EmbeddingService
from .qdrant_client import QdrantDB

class RAGPipeline:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.embedding_service = EmbeddingService()
        self.vector_store = QdrantDB()
        
    def process_documents(self, documents: List[str]):
        """Process documents and store in vector database"""
        pass
    
    def query(self, query: str):
        """Query the RAG system"""
        pass
