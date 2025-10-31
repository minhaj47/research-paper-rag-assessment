from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time

from ..services.rag_pipeline import RAGPipeline
from ..services.database_service import DatabaseService
from ..models.database import get_db

router = APIRouter()
rag_pipeline = RAGPipeline()

class Query(BaseModel):
    query: str
    top_k: int = 5

@router.post("/upload")
async def upload_papers(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload and process one or multiple research papers"""
    results = []
    
    for file in files:
        try:
            # Check if paper already exists
            existing_paper = DatabaseService.get_paper_by_filename(db, file.filename)
            if existing_paper:
                results.append({
                    "status": "error",
                    "filename": file.filename,
                    "message": f"Paper '{file.filename}' already exists in the database",
                    "paper_id": existing_paper.id
                })
                continue
            
            content = await file.read()
            result = await rag_pipeline.process_and_store_document(content, file.filename)
            
            # Prepare sections metadata for database
            sections_metadata = {
                section: {
                    "chunk_count": len(section_data["chunks"]),
                    "start_page": section_data["start_page"],
                    "preview": section_data["chunks"][0][:200] if section_data["chunks"] else ""
                }
                for section, section_data in result["sections"].items()
            }
            
            # Save paper metadata to database
            paper_data = {
                "filename": file.filename,
                "title": result["metadata"]["title"],
                "author": result["metadata"]["author"],
                "page_count": result["metadata"]["page_count"],
                "file_size": len(content),
                "content_type": file.content_type,
                "total_chunks": result["stored_chunks"],
                "sections_metadata": sections_metadata
            }
            
            paper = DatabaseService.create_paper(db, paper_data)
            
            # Update vector store with paper_id (re-process with paper_id)
            await rag_pipeline.process_and_store_document(content, file.filename, paper.id)
            
            results.append({
                "status": "success",
                "filename": file.filename,
                "paper_id": paper.id,
                "metadata": result["metadata"],
                "sections": sections_metadata,
                "total_chunks": result["stored_chunks"],
                "content_type": file.content_type,
                "file_size": len(content)
            })
        except Exception as e:
            results.append({
                "status": "error",
                "filename": file.filename,
                "message": str(e)
            })
    
    # Return single result if only one file, otherwise return batch results
    if len(results) == 1:
        return results[0]
    else:
        return {
            "status": "completed",
            "total": len(files),
            "results": results
        }


@router.post("/query")
async def query_papers(
    query: str, 
    top_k: int = 5,
    paper_ids: List[int] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Query the RAG system with a question, optionally filtered by paper IDs"""
    try:
        start_time = time.time()
        result = await rag_pipeline.query(query, top_k, paper_ids)
        response_time = time.time() - start_time
        
        # Extract paper IDs from citations
        papers_referenced = list(set([
            citation.get("paper_title", "") 
            for citation in result.get("citations", [])
        ]))
        
        # Save query to database
        query_data = {
            "query_text": query,
            "answer": result["answer"],
            "top_k": top_k,
            "response_time": response_time,
            "papers_referenced": papers_referenced,
            "confidence_score": result.get("confidence")
        }
        DatabaseService.create_query(db, query_data)
        
        return {
            **result,
            "response_time": round(response_time, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/papers")
async def list_papers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all papers in the database"""
    papers = DatabaseService.list_papers(db, skip, limit)
    return {
        "total": len(papers),
        "papers": [
            {
                "id": paper.id,
                "filename": paper.filename,
                "title": paper.title,
                "author": paper.author,
                "page_count": paper.page_count,
                "total_chunks": paper.total_chunks,
                "upload_date": paper.upload_date.isoformat()
            }
            for paper in papers
        ]
    }

@router.get("/papers/{paper_id}")
async def get_paper(paper_id: int, db: Session = Depends(get_db)):
    """Get details of a specific paper"""
    paper = DatabaseService.get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "id": paper.id,
        "filename": paper.filename,
        "title": paper.title,
        "author": paper.author,
        "page_count": paper.page_count,
        "file_size": paper.file_size,
        "content_type": paper.content_type,
        "total_chunks": paper.total_chunks,
        "upload_date": paper.upload_date.isoformat(),
        "sections": paper.sections_metadata
    }

@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    """Delete a paper from the system"""
    paper = DatabaseService.get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Delete from database
    success = DatabaseService.delete_paper(db, paper_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete paper")
    
    # TODO: Also delete from Qdrant vector store
    # rag_pipeline.delete_paper_vectors(paper.filename)
    
    return {"status": "success", "message": f"Paper {paper_id} deleted"}

@router.get("/papers/{paper_id}/stats")
async def get_paper_stats(paper_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific paper"""
    paper = DatabaseService.get_paper_by_id(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "paper_id": paper.id,
        "title": paper.title,
        "total_chunks": paper.total_chunks,
        "sections": paper.sections_metadata,
        "upload_date": paper.upload_date.isoformat()
    }

@router.get("/queries/history")
async def query_history(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent query history"""
    queries = DatabaseService.get_query_history(db, limit)
    return {
        "total": len(queries),
        "queries": [
            {
                "id": q.id,
                "query_text": q.query_text,
                "answer": q.answer[:200] + "..." if q.answer and len(q.answer) > 200 else q.answer,
                "response_time": q.response_time,
                "papers_referenced": q.papers_referenced,
                "created_at": q.created_at.isoformat()
            }
            for q in queries
        ]
    }

@router.get("/analytics/popular")
async def popular_queries(limit: int = 10, db: Session = Depends(get_db)):
    """Get most popular query topics"""
    popular = DatabaseService.get_popular_queries(db, limit)
    return {
        "popular_queries": popular
    }