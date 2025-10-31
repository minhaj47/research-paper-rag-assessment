from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(
    title="Research Paper RAG API",
    description="RAG system for querying research papers",
    version="0.1.0"
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "RAG system running successfully!"}

@app.get("/health")
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "service": "Research Paper RAG API",
        "version": "0.1.0"
    }
