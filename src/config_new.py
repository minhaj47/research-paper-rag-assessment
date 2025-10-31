"""
Configuration Management Module

This module handles all application configuration using environment variables
with sensible defaults and validation.
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ================================
# Project Paths
# ================================

PROJECT_ROOT = Path(__file__).parent.parent
UPLOAD_DIR = PROJECT_ROOT / os.getenv("UPLOAD_DIR", "uploads")
TEMP_DIR = PROJECT_ROOT / os.getenv("TEMP_DIR", "temp")
LOG_DIR = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")
VECTOR_STORE_PATH = PROJECT_ROOT / "vector_store"

# Create directories if they don't exist
for directory in [UPLOAD_DIR, TEMP_DIR, LOG_DIR, VECTOR_STORE_PATH]:
    directory.mkdir(parents=True, exist_ok=True)

# ================================
# Database Configuration
# ================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rag_user:rag_password@localhost:5432/research_papers_db"
)

# ================================
# Qdrant Configuration
# ================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "research_papers")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # Optional, for Qdrant Cloud

# ================================
# LLM Configuration
# ================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # 'ollama' or 'deepseek'
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")

# DeepSeek configuration (if using DeepSeek)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# LLM generation parameters
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))

# ================================
# Embedding Configuration
# ================================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

# ================================
# Document Processing
# ================================

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "pdf").split(",")

# ================================
# API Server Configuration
# ================================

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "60"))  # requests per minute

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ================================
# Application Settings
# ================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_REQUESTS = os.getenv("LOG_REQUESTS", "true").lower() == "true"

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DETAILED_ERRORS = os.getenv("DETAILED_ERRORS", "true").lower() == "true"
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true").lower() == "true"

# ================================
# Vector Search Configuration
# ================================

DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
MIN_SIMILARITY_SCORE = float(os.getenv("MIN_SIMILARITY_SCORE", "0.7"))
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "20"))

# ================================
# Cache Configuration
# ================================

ENABLE_CACHE = os.getenv("ENABLE_CACHE", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds

# ================================
# Security Configuration
# ================================

API_KEY = os.getenv("API_KEY")  # Optional API key for authentication
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
ENABLE_HTTPS = os.getenv("ENABLE_HTTPS", "false").lower() == "true"

# ================================
# Monitoring & Analytics
# ================================

ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ANALYTICS_RETENTION_DAYS = int(os.getenv("ANALYTICS_RETENTION_DAYS", "90"))

# ================================
# Validation Functions
# ================================

def validate_config() -> List[str]:
    """
    Validate configuration and return list of warnings/errors.
    
    Returns:
        List of validation messages
    """
    messages = []
    
    # Check database URL
    if not DATABASE_URL or DATABASE_URL == "":
        messages.append("ERROR: DATABASE_URL is not set")
    
    # Check LLM configuration
    if LLM_PROVIDER == "ollama":
        if not OLLAMA_HOST:
            messages.append("WARNING: OLLAMA_HOST is not set, using default")
        if not OLLAMA_MODEL:
            messages.append("WARNING: OLLAMA_MODEL is not set, using default")
    elif LLM_PROVIDER == "deepseek":
        if not DEEPSEEK_API_KEY:
            messages.append("ERROR: DEEPSEEK_API_KEY is required for DeepSeek provider")
    else:
        messages.append(f"ERROR: Invalid LLM_PROVIDER '{LLM_PROVIDER}'. Must be 'ollama' or 'deepseek'")
    
    # Check embedding dimension matches model
    expected_dims = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "multi-qa-MiniLM-L6-cos-v1": 384
    }
    if EMBEDDING_MODEL in expected_dims:
        if EMBEDDING_DIMENSION != expected_dims[EMBEDDING_MODEL]:
            messages.append(
                f"WARNING: EMBEDDING_DIMENSION ({EMBEDDING_DIMENSION}) doesn't match "
                f"{EMBEDDING_MODEL} expected dimension ({expected_dims[EMBEDDING_MODEL]})"
            )
    
    # Check chunk parameters
    if CHUNK_OVERLAP >= CHUNK_SIZE:
        messages.append("ERROR: CHUNK_OVERLAP must be less than CHUNK_SIZE")
    
    # Check security in production
    if ENVIRONMENT == "production":
        if not API_KEY and not JWT_SECRET:
            messages.append("WARNING: No authentication configured for production!")
        if not ENABLE_HTTPS:
            messages.append("WARNING: HTTPS not enabled in production!")
        if DEBUG:
            messages.append("ERROR: DEBUG mode should be disabled in production!")
    
    return messages


def print_config_summary():
    """Print a summary of the current configuration."""
    print("\n" + "="*60)
    print("Configuration Summary".center(60))
    print("="*60)
    
    print(f"\n📁 Project Root: {PROJECT_ROOT}")
    print(f"🌍 Environment: {ENVIRONMENT}")
    print(f"📊 Log Level: {LOG_LEVEL}")
    
    print(f"\n🗄️  Database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    print(f"🔍 Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"   Collection: {QDRANT_COLLECTION_NAME}")
    
    print(f"\n🤖 LLM Provider: {LLM_PROVIDER}")
    if LLM_PROVIDER == "ollama":
        print(f"   Ollama: {OLLAMA_HOST}")
        print(f"   Model: {OLLAMA_MODEL}")
    
    print(f"\n🧠 Embedding Model: {EMBEDDING_MODEL}")
    print(f"   Dimensions: {EMBEDDING_DIMENSION}")
    print(f"   Batch Size: {EMBEDDING_BATCH_SIZE}")
    
    print(f"\n📄 Document Processing:")
    print(f"   Chunk Size: {CHUNK_SIZE} tokens")
    print(f"   Overlap: {CHUNK_OVERLAP} tokens")
    print(f"   Max File Size: {MAX_FILE_SIZE_MB} MB")
    
    print(f"\n🌐 API Server:")
    print(f"   Host: {API_HOST}:{API_PORT}")
    print(f"   Reload: {API_RELOAD}")
    print(f"   Rate Limit: {API_RATE_LIMIT} req/min")
    
    print(f"\n🔍 Search Configuration:")
    print(f"   Default Top-K: {DEFAULT_TOP_K}")
    print(f"   Min Similarity: {MIN_SIMILARITY_SCORE}")
    
    print("\n" + "="*60 + "\n")
    
    # Run validation and print any issues
    validation_messages = validate_config()
    if validation_messages:
        print("⚠️  Configuration Issues:")
        for msg in validation_messages:
            print(f"   {msg}")
        print()


# ================================
# Configuration Class (Optional)
# ================================

class Config:
    """
    Configuration class for easy access to all settings.
    Can be used as an alternative to individual constants.
    """
    
    # Paths
    PROJECT_ROOT = PROJECT_ROOT
    UPLOAD_DIR = UPLOAD_DIR
    TEMP_DIR = TEMP_DIR
    LOG_DIR = LOG_DIR
    VECTOR_STORE_PATH = VECTOR_STORE_PATH
    
    # Database
    DATABASE_URL = DATABASE_URL
    
    # Qdrant
    QDRANT_HOST = QDRANT_HOST
    QDRANT_PORT = QDRANT_PORT
    QDRANT_COLLECTION_NAME = QDRANT_COLLECTION_NAME
    QDRANT_API_KEY = QDRANT_API_KEY
    
    # LLM
    LLM_PROVIDER = LLM_PROVIDER
    OLLAMA_HOST = OLLAMA_HOST
    OLLAMA_MODEL = OLLAMA_MODEL
    DEEPSEEK_API_KEY = DEEPSEEK_API_KEY
    DEEPSEEK_MODEL = DEEPSEEK_MODEL
    LLM_TEMPERATURE = LLM_TEMPERATURE
    LLM_MAX_TOKENS = LLM_MAX_TOKENS
    LLM_TOP_P = LLM_TOP_P
    
    # Embeddings
    EMBEDDING_MODEL = EMBEDDING_MODEL
    EMBEDDING_DIMENSION = EMBEDDING_DIMENSION
    EMBEDDING_BATCH_SIZE = EMBEDDING_BATCH_SIZE
    
    # Document Processing
    CHUNK_SIZE = CHUNK_SIZE
    CHUNK_OVERLAP = CHUNK_OVERLAP
    MAX_FILE_SIZE_MB = MAX_FILE_SIZE_MB
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_BYTES
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    
    # API
    API_HOST = API_HOST
    API_PORT = API_PORT
    API_RELOAD = API_RELOAD
    API_RATE_LIMIT = API_RATE_LIMIT
    CORS_ORIGINS = CORS_ORIGINS
    
    # Application
    ENVIRONMENT = ENVIRONMENT
    LOG_LEVEL = LOG_LEVEL
    LOG_FILE = LOG_FILE
    LOG_REQUESTS = LOG_REQUESTS
    DEBUG = DEBUG
    DETAILED_ERRORS = DETAILED_ERRORS
    ENABLE_DOCS = ENABLE_DOCS
    
    # Search
    DEFAULT_TOP_K = DEFAULT_TOP_K
    MIN_SIMILARITY_SCORE = MIN_SIMILARITY_SCORE
    MAX_TOP_K = MAX_TOP_K
    
    # Cache
    ENABLE_CACHE = ENABLE_CACHE
    REDIS_HOST = REDIS_HOST
    REDIS_PORT = REDIS_PORT
    REDIS_DB = REDIS_DB
    REDIS_PASSWORD = REDIS_PASSWORD
    CACHE_TTL = CACHE_TTL
    
    # Security
    API_KEY = API_KEY
    JWT_SECRET = JWT_SECRET
    JWT_ALGORITHM = JWT_ALGORITHM
    JWT_EXPIRATION_HOURS = JWT_EXPIRATION_HOURS
    ENABLE_HTTPS = ENABLE_HTTPS
    
    # Monitoring
    ENABLE_MONITORING = ENABLE_MONITORING
    ENABLE_ANALYTICS = ENABLE_ANALYTICS
    ANALYTICS_RETENTION_DAYS = ANALYTICS_RETENTION_DAYS
    
    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration."""
        return validate_config()
    
    @classmethod
    def print_summary(cls):
        """Print configuration summary."""
        print_config_summary()


# Run validation on import (in development mode)
if __name__ == "__main__":
    print_config_summary()
    validation_messages = validate_config()
    
    if any("ERROR" in msg for msg in validation_messages):
        print("❌ Configuration has errors!")
        exit(1)
    else:
        print("✅ Configuration is valid!")
