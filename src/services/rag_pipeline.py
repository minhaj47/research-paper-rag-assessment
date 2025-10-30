from typing import List, Dict, Any
from .document_processor import DocumentProcessor
from .embedding_service import EmbeddingService
from .qdrant_client import QdrantDB
import asyncio

class RAGPipeline:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.embedding_service = EmbeddingService()
        self.vector_store = QdrantDB()
        
        # Initialize Qdrant collection
        self.vector_store.create_collection()
        
    async def process_and_store_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process document and store chunks in vector database"""
        # Process the PDF
        processed_doc = await self.document_processor.process_pdf(file_content)
        
        # Prepare chunks and metadata for storage
        all_chunks = []
        all_metadata = []
        
        for section_name, section_data in processed_doc["sections"].items():
            chunks = section_data["chunks"]
            start_page = section_data["start_page"]
            
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadata.append({
                    "filename": filename,
                    "section": section_name,
                    "page": start_page,
                    "title": processed_doc["metadata"]["title"],
                    "author": processed_doc["metadata"]["author"],
                    "chunk_index": i
                })
        
        # Generate embeddings for all chunks
        embeddings = await asyncio.to_thread(
            self._generate_embeddings_batch, all_chunks
        )
        
        
        # Store in Qdrant
        stored_count = await asyncio.to_thread(
            self.vector_store.store_chunks, all_chunks, embeddings, all_metadata
        )
        
        return {
            **processed_doc,
            "stored_chunks": stored_count,
            "status": "success"
        }
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        return [self.embedding_service.get_embeddings(text).tolist() for text in texts]
    
    async def query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Query the RAG system"""
        # Generate query embedding
        query_embedding = await asyncio.to_thread(
            self.embedding_service.get_embeddings, query
        )
        
        # Search similar chunks
        results = await asyncio.to_thread(
            self.vector_store.search_similar, 
            query_embedding.tolist(), 
            top_k
        )
        
        # Format results
        context_chunks = []
        citations = []
        
        for result in results:
            payload = result.payload
            context_chunks.append({
                "text": payload["text"],
                "score": result.score,
                "metadata": {
                    "filename": payload["filename"],
                    "section": payload["section"],
                    "page": payload["page"],
                    "title": payload.get("title", ""),
                    "author": payload.get("author", "")
                }
            })
            
            citations.append({
                "paper_title": payload.get("title", payload["filename"]),
                "section": payload["section"],
                "page": payload["page"],
                "relevance_score": result.score
            })
        
        return {
            "query": query,
            "context_chunks": context_chunks,
            "citations": citations,
            "total_results": len(results)
        }