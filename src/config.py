import os
from dotenv import load_dotenv

load_dotenv()

# Model Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_STORE_PATH = "vector_store"

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
