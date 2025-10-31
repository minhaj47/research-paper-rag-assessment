from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny
from typing import List, Dict, Any, Optional
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
        """Create a collection for research papers if it doesn't exist"""
        try:
            # Check if collection already exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name in collection_names:
                print(f"✅ Collection '{self.collection_name}' already exists")
                return
            
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"✅ Collection '{self.collection_name}' created successfully")
        except Exception as e:
            print(f"⚠️  Collection creation warning: {e}")
    
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
                    "paper_id": meta.get("paper_id"),  # Add paper_id for filtering
                    **meta
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return len(points)
    
    def search_similar(self, query_embedding: List[float], limit: int = 5, score_threshold: float = 0.3, paper_ids: Optional[List[int]] = None):
        """Search for similar chunks with optional paper_ids filter"""
        query_filter = None
        
        # Add filter for specific papers if paper_ids provided
        if paper_ids and len(paper_ids) > 0:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="paper_id",
                        match=MatchAny(any=paper_ids)
                    )
                ]
            )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter
        )
        return results