# 🎓 Research Paper RAG Assistant

A production-ready RAG (Retrieval-Augmented Generation) system that helps researchers efficiently query and understand academic papers using vector search, PostgreSQL, and LLMs.

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│      FastAPI Application        │
│  ┌───────────────────────────┐  │
│  │   Document Processor      │  │
│  │  - PDF extraction         │  │
│  │  - Chunking strategy      │  │
│  │  - Embedding generation   │  │
│  └───────────────────────────┘  │
│                                  │
│  ┌───────────────────────────┐  │
│  │   RAG Pipeline            │  │
│  │  - Query understanding    │  │
│  │  - Vector retrieval       │  │
│  │  - Context assembly       │  │
│  │  - LLM generation         │  │
│  └───────────────────────────┘  │
└────┬──────────────────┬─────────┘
     │                  │
     ▼                  ▼
┌─────────┐      ┌──────────────┐
│ Qdrant  │      │ PostgreSQL   │
│ Vector  │      │ (Metadata)   │
│ Store   │      │              │
└─────────┘      └──────────────┘
     │
     ▼
┌─────────────┐
│ Ollama      │
│ (LLM)       │
└─────────────┘
```

## ✨ Features

- ✅ **PDF Upload & Processing**: Extract and chunk research papers with section awareness
- ✅ **Vector Search**: Fast semantic search using Qdrant
- ✅ **Intelligent Q&A**: LLM-powered answers with citations
- ✅ **PostgreSQL Metadata Storage**: Track papers, queries, and analytics
- ✅ **RESTful API**: Complete API for paper management and querying
- ✅ **Docker Compose**: One-command setup for all services
- ✅ **Query History & Analytics**: Track usage patterns and popular queries

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Ollama (for LLM)

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/research-paper-rag-assessment.git
cd research-paper-rag-assessment
```

### 2. Start Docker Services

```bash
docker-compose up -d
```

This starts:

- **Qdrant** on port 6333 (vector database)
- **PostgreSQL** on port 5432 (metadata storage)

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 4. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (defaults work for local development)
```

### 5. Initialize Database

```bash
python src/init_db.py
```

### 6. Install and Start Ollama

```bash
# Install Ollama (if not already installed)
# macOS/Linux:
curl https://ollama.ai/install.sh | sh

# Pull the LLM model
ollama pull llama3:latest

# Start Ollama (runs in background)
ollama serve
```

### 7. Run the Application

```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Upload Paper

```bash
POST /api/upload
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sample_papers/paper_1.pdf"
```

**Response:**

```json
{
  "status": "success",
  "paper_id": 1,
  "filename": "paper_1.pdf",
  "metadata": {
    "title": "Machine Learning Fundamentals",
    "author": "John Doe",
    "page_count": 15
  },
  "total_chunks": 45,
  "sections": {
    "Abstract": { "chunk_count": 2, "start_page": 1 },
    "Introduction": { "chunk_count": 5, "start_page": 2 }
  }
}
```

### Query Papers

```bash
POST /api/query?query=your_question&top_k=5
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/query?query=What%20is%20machine%20learning?&top_k=5"
```

**Response:**

```json
{
  "answer": "Machine learning is...",
  "citations": [
    {
      "paper_title": "paper_1.pdf",
      "section": "Introduction",
      "page": 2,
      "relevance_score": 0.89
    }
  ],
  "sources_used": ["paper_1.pdf"],
  "response_time": 2.45
}
```

### List Papers

```bash
GET /api/papers
```

**Example:**

```bash
curl "http://localhost:8000/api/papers"
```

### Get Paper Details

```bash
GET /api/papers/{paper_id}
```

**Example:**

```bash
curl "http://localhost:8000/api/papers/1"
```

### Delete Paper

```bash
DELETE /api/papers/{paper_id}
```

**Example:**

```bash
curl -X DELETE "http://localhost:8000/api/papers/1"
```

### Get Paper Stats

```bash
GET /api/papers/{paper_id}/stats
```

### Query History

```bash
GET /api/queries/history?limit=50
```

**Example:**

```bash
curl "http://localhost:8000/api/queries/history?limit=20"
```

### Popular Queries

```bash
GET /api/analytics/popular?limit=10
```

**Example:**

```bash
curl "http://localhost:8000/api/analytics/popular"
```

## 🧪 Testing

Upload and test with sample papers:

```bash
# Upload all sample papers
for file in sample_papers/*.pdf; do
  curl -X POST "http://localhost:8000/api/upload" -F "file=@$file"
done

# Test queries
curl -X POST "http://localhost:8000/api/query?query=What%20are%20transformers?&top_k=5"
```

## 🗂️ Project Structure

```
research-paper-rag-assessment/
├── src/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration settings
│   ├── init_db.py                 # Database initialization
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # API endpoints
│   ├── models/
│   │   ├── database.py            # SQLAlchemy models
│   │   └── document.py            # Document models
│   └── services/
│       ├── document_processor.py  # PDF processing & chunking
│       ├── embedding_service.py   # Text embeddings
│       ├── qdrant_client.py       # Vector database client
│       ├── rag_pipeline.py        # RAG orchestration
│       └── database_service.py    # Database operations
├── sample_papers/                 # Sample research papers
├── docker-compose.yml             # Docker services
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## 🔧 Configuration

Edit `.env` to customize:

```bash
# Database
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/research_papers_db

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# LLM
LLM_MODEL=llama3:latest
```

## 🛠️ Tech Stack

| Component          | Technology            | Purpose                      |
| ------------------ | --------------------- | ---------------------------- |
| **Backend**        | FastAPI               | RESTful API framework        |
| **Vector DB**      | Qdrant                | Semantic search & embeddings |
| **Database**       | PostgreSQL            | Metadata & query history     |
| **LLM**            | Ollama (llama3)       | Answer generation            |
| **Embeddings**     | sentence-transformers | Text vectorization           |
| **PDF Processing** | PyMuPDF               | PDF text extraction          |
| **ORM**            | SQLAlchemy            | Database operations          |

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Remove volumes (clean slate)
docker-compose down -v
```

## 📊 Database Schema

### Papers Table

- `id`: Primary key
- `filename`: Unique filename
- `title`: Paper title
- `author`: Author name(s)
- `page_count`: Number of pages
- `file_size`: File size in bytes
- `content_type`: MIME type
- `total_chunks`: Number of text chunks
- `upload_date`: Upload timestamp
- `sections_metadata`: JSON of section information

### Queries Table

- `id`: Primary key
- `query_text`: User's question
- `answer`: Generated answer
- `top_k`: Number of results retrieved
- `response_time`: Query processing time
- `papers_referenced`: List of papers used
- `created_at`: Query timestamp
- `confidence_score`: Answer confidence (optional)

## 🚨 Troubleshooting

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
docker ps

# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Qdrant Connection Error

```bash
# Check if Qdrant is running
docker ps

# Restart Qdrant
docker-compose restart qdrant
```

### Ollama Not Responding

```bash
# Check if Ollama is running
ollama list

# Restart Ollama
pkill ollama && ollama serve
```

### Import Errors

```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 🎯 Future Enhancements

- [ ] Web UI for paper upload and querying
- [ ] Advanced analytics dashboard
- [ ] Multi-paper comparison
- [ ] Export results to PDF/Markdown
- [ ] API authentication
- [ ] Caching for faster queries
- [ ] Support for more file formats (DOCX, TXT)

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ for AI-powered research
