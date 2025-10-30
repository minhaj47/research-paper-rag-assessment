from sqlalchemy.orm import Session
from src.models.database import Paper, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseService:
    @staticmethod
    def create_paper(db: Session, paper_data: Dict[str, Any]) -> Paper:
        """Create a new paper record"""
        paper = Paper(
            filename=paper_data["filename"],
            title=paper_data["title"],
            author=paper_data["author"],
            page_count=paper_data["page_count"],
            file_size=paper_data.get("file_size"),
            content_type=paper_data.get("content_type"),
            total_chunks=paper_data["total_chunks"],
            sections_metadata=paper_data.get("sections_metadata", {})
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)
        return paper
    
    @staticmethod
    def get_paper_by_filename(db: Session, filename: str) -> Optional[Paper]:
        """Get paper by filename"""
        return db.query(Paper).filter(Paper.filename == filename).first()
    
    @staticmethod
    def get_paper_by_id(db: Session, paper_id: int) -> Optional[Paper]:
        """Get paper by ID"""
        return db.query(Paper).filter(Paper.id == paper_id).first()
    
    @staticmethod
    def list_papers(db: Session, skip: int = 0, limit: int = 100) -> List[Paper]:
        """List all papers"""
        return db.query(Paper).offset(skip).limit(limit).all()
    
    @staticmethod
    def delete_paper(db: Session, paper_id: int) -> bool:
        """Delete a paper"""
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if paper:
            db.delete(paper)
            db.commit()
            return True
        return False
    
    @staticmethod
    def create_query(db: Session, query_data: Dict[str, Any]) -> Query:
        """Create a new query record"""
        query = Query(
            query_text=query_data["query_text"],
            answer=query_data.get("answer"),
            top_k=query_data.get("top_k", 5),
            response_time=query_data.get("response_time"),
            papers_referenced=query_data.get("papers_referenced", []),
            confidence_score=query_data.get("confidence_score")
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        return query
    
    @staticmethod
    def get_query_history(db: Session, limit: int = 50) -> List[Query]:
        """Get recent query history"""
        return db.query(Query).order_by(Query.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_popular_queries(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular query patterns"""
        # This is a simplified version - you could enhance with more sophisticated analytics
        queries = db.query(Query.query_text).limit(100).all()
        # Count similar queries and return top ones
        from collections import Counter
        query_counts = Counter([q[0] for q in queries])
        return [{"query": q, "count": c} for q, c in query_counts.most_common(limit)]
