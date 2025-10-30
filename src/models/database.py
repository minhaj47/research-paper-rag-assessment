from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.config import DATABASE_URL

Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(500))
    page_count = Column(Integer)
    file_size = Column(Integer)
    content_type = Column(String(100))
    total_chunks = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    sections_metadata = Column(JSON)  # Store section info as JSON

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    answer = Column(Text)
    top_k = Column(Integer, default=5)
    response_time = Column(Float)  # in seconds
    papers_referenced = Column(JSON)  # List of paper IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float)

# Database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
