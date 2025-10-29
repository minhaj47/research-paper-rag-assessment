from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class QdrantDB:
    def __init__(self):
        self.client = QdrantClient(":memory:")  # Using in-memory storage for development
        
    def create_collection(self, collection_name: str, vector_size: int):
        """Create a new collection"""
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
