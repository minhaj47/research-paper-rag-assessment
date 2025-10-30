import os
from dotenv import load_dotenv

load_dotenv()

# Model Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_STORE_PATH = "vector_store"

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rag_user:rag_password@localhost:5432/research_papers_db"
)

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "llama3:latest")
