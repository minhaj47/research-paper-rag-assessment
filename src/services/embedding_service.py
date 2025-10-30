from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def get_embeddings(self, text: str):
        """Generate embeddings for the given text (normalized for cosine search)"""
        return self.model.encode(text, normalize_embeddings=True)