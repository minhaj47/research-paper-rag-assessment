from fastapi import APIRouter, UploadFile, File
from typing import List
from pydantic import BaseModel
from src.services.rag_pipeline import RAGPipeline

router = APIRouter()
rag_pipeline = RAGPipeline()

class Query(BaseModel):
    query: str
    top_k: int = 5

@router.post("/upload")
async def upload_papers(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = await rag_pipeline.process_and_store_document(content, file.filename)
        
        return {
            "status": "success",
            "filename": file.filename,
            "metadata": result["metadata"],
            "sections": {
                section: {
                    "chunk_count": len(section_data["chunks"]),
                    "start_page": section_data["start_page"],
                    "preview": section_data["chunks"][0][:200] if section_data["chunks"] else ""
                }
                for section, section_data in result["sections"].items()
            },
            "total_chunks": result["stored_chunks"],
            "content_type": file.content_type,
            "file_size": len(content)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/query")
async def query_papers(query: Query):
    """Query the uploaded research papers"""
    try:
        result = await rag_pipeline.query(query.query, query.top_k)
        
        # Simple response format (you can enhance this with LLM generation later)
        response_text = f"Found {len(result['context_chunks'])} relevant chunks for query: '{query.query}'"
        
        return {
            "status": "success",
            "query": query.query,
            "response": response_text,
            "context": result["context_chunks"],
            "citations": result["citations"]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}