from typing import List, Dict, Any
from .document_processor import DocumentProcessor
from .embedding_service import EmbeddingService
from .qdrant_client import QdrantDB
import asyncio
import ollama

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
        
        # Prepare context for LLM
        context = "\n\n".join([
            f"[Source {i+1} - {chunk['metadata']['title']}, Section: {chunk['metadata']['section']}, Page: {chunk['metadata']['page']}]\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Generate answer using Ollama
        prompt = f"""You are a research paper assistant. Answer the question based on the provided context from research papers.

                    Context:
                    {context}

                    Question: {query}

                    Instructions:
                    - Answer based only on the provided context
                    - Be specific and cite relevant sections
                    - If the answer cannot be found in the context, say so clearly
                    - Keep your answer concise and accurate

                    Answer:"""
        
        # Call Ollama (runs in thread to avoid blocking)
        llm_response = await asyncio.to_thread(
            self._generate_llm_response, prompt
        )
        
        return {
            "query": query,
            "answer": llm_response,
            "context_chunks": context_chunks,
            "citations": citations,
            "total_results": len(results)
        }
    
    def _generate_llm_response(self, prompt: str) -> str:
        """Generate response using Ollama"""
        try:
            response = ollama.chat(
                model='llama3:latest',  
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error generating response: {str(e)}"