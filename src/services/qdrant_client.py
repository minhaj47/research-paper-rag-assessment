from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import uuid
from src.config import QDRANT_HOST, QDRANT_PORT

class QdrantDB:
    def __init__(self, host: str = None, port: int = None):
        self.client = QdrantClient(
            host=host or QDRANT_HOST, 
            port=port or QDRANT_PORT
        )
        self.collection_name = "research_papers"
        
    def create_collection(self, vector_size: int = 384):
        """Create a collection for research papers"""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
        except Exception as e:
            # Collection might already exist
            print(f"Collection creation info: {e}")
    
    def store_chunks(self, chunks: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
        """Store document chunks with embeddings and metadata"""
        points = []
        for i, (chunk, embedding, meta) in enumerate(zip(chunks, embeddings, metadata)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": chunk,
                    "filename": meta.get("filename", ""),
                    "section": meta.get("section", ""),
                    "page": meta.get("page", 0),
                    "chunk_index": i,
                    **meta
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return len(points)
    
    def search_similar(self, query_embedding: List[float], limit: int = 5, score_threshold: float = 0.3):
        """Search for similar chunks"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        return results