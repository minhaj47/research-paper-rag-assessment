from fastapi import APIRouter, UploadFile, File
from typing import List
from pydantic import BaseModel
from src.services.document_processor import DocumentProcessor

router = APIRouter()
doc_processor = DocumentProcessor()

class Query(BaseModel):
    query: str


@router.post("/upload")
async def upload_papers(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = await doc_processor.process_pdf(content)
        
        # Count total chunks across all sections
        total_chunks = sum(len(section["chunks"]) for section in result["sections"].values())
        
        return {
            "status": "success",
            "filename": file.filename,
            "metadata": result["metadata"],
            "sections": {
                section: {
                    "chunk_count": len(content["chunks"]),
                    "start_page": content["start_page"],
                    "preview": content["chunks"][0] if content["chunks"] else ""
                }
                for section, content in result["sections"].items()
            },
            "total_chunks": total_chunks,
            "content_type": file.content_type,
            "file_size": len(content)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/query")
async def query_papers(query: Query):
    """
    Query the uploaded research papers
    """
    return {"response": f"Placeholder response for query: {query.query}"}
