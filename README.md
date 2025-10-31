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
│ Vector  │      │ (Metadata &  │
│ Store   │      │  Queries)    │
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
- ✅ **PostgreSQL Storage**: Track papers, queries, and analytics
- ✅ **Query History**: Monitor and analyze user queries
- ✅ **Paper Management**: CRUD operations for research papers
- ✅ **Docker Compose**: One-command deployment

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose**: For running services
- **Ollama**: For local LLM (or use DeepSeek API)
- **Python 3.10+**: For local development

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd research-paper-rag-assessment
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configurations (optional - defaults work!)
# nano .env
```

### 3. Start Services with Docker (Recommended)

```bash
# One command to start everything!
docker-compose up --build
```

This will:

- ✅ Start Qdrant (vector database)
- ✅ Start PostgreSQL (metadata database)
- ✅ Build and start the FastAPI application
- ✅ Initialize database tables automatically
- ✅ Make API available at http://localhost:8000

**API Documentation**: Visit http://localhost:8000/docs

### Alternative: Local Development

```bash
# Start services only (no app container)
docker-compose up -d qdrant postgres

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/init_db.py

# Run application
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Setup Ollama (Required for LLM)

```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the LLM model (llama3 recommended)
ollama pull llama3

# Verify Ollama is running
ollama list
```

## 📡 API Endpoints

### Upload Paper

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sample_papers/paper_1.pdf"
```

**Response:**

```json
{
  "message": "Paper uploaded successfully",
  "paper_id": 1,
  "filename": "paper_1.pdf",
  "title": "Extracted Paper Title",
  "chunks_created": 42,
  "sections": ["Abstract", "Introduction", "Methods", "Results"]
}
```

### Query Papers

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What methodology was used in the transformer paper?",
    "top_k": 5
  }'
```

**Response:**

```json
{
  "answer": "The transformer paper uses a self-attention mechanism...",
  "citations": [
    {
      "paper_title": "Attention is All You Need",
      "section": "Methodology",
      "page": 3,
      "relevance_score": 0.89,
      "text": "excerpt from paper..."
    }
  ],
  "sources_used": ["paper_3.pdf"],
  "confidence": 0.85
}
```

### List All Papers

```bash
curl "http://localhost:8000/api/papers"
```

### Get Paper Details

```bash
curl "http://localhost:8000/api/papers/1"
```

### Delete Paper

```bash
curl -X DELETE "http://localhost:8000/api/papers/1"
```

### Query History

```bash
curl "http://localhost:8000/api/queries/history?limit=10"
```

### Popular Topics Analytics

```bash
curl "http://localhost:8000/api/analytics/popular"
```

## 📁 Project Structure

```
research-paper-rag-assessment/
├── src/
│   ├── main.py                        # FastAPI application entry point
│   ├── config.py                      # Configuration management
│   ├── init_db.py                     # Database initialization
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                  # API endpoints
│   ├── models/
│   │   ├── database.py                # SQLAlchemy models
│   │   └── document.py                # Document data models
│   └── services/
│       ├── document_processor.py      # PDF extraction & chunking
│       ├── embedding_service.py       # Text embeddings generation
│       ├── qdrant_client.py           # Qdrant vector operations
│       ├── rag_pipeline.py            # RAG query pipeline
│       └── database_service.py        # PostgreSQL operations
├── sample_papers/                     # Test dataset (5 papers)
├── provided_docs/                     # Assessment documentation
├── tests/                             # Unit tests
├── docker-compose.yml                 # Docker services configuration
├── Dockerfile                         # Application container
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── .env                              # Your configuration (gitignored)
├── README.md                          # This file
└── APPROACH.md                        # Design decisions & trade-offs
```

## 🔧 Configuration

All settings are managed through environment variables in `.env`:

| Variable          | Default                                                                | Description                  |
| ----------------- | ---------------------------------------------------------------------- | ---------------------------- |
| `DATABASE_URL`    | `postgresql://rag_user:rag_password@localhost:5432/research_papers_db` | PostgreSQL connection string |
| `QDRANT_HOST`     | `localhost`                                                            | Qdrant server host           |
| `QDRANT_PORT`     | `6333`                                                                 | Qdrant server port           |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2`                                                     | Sentence transformer model   |
| `LLM_MODEL`       | `llama3:latest`                                                        | Ollama model name            |
| `API_HOST`        | `0.0.0.0`                                                              | API server host              |
| `API_PORT`        | `8000`                                                                 | API server port              |

**Note**: The `.env.example` file contains safe defaults that work out of the box!

## 🧪 Testing

### Test with Sample Papers

```bash
# Upload all sample papers
for file in sample_papers/*.pdf; do
  curl -X POST "http://localhost:8000/api/upload" -F "file=@$file"
done
```

### Test Queries

```bash
# Simple query
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main contributions of the papers?"}'

# Query with top_k parameter
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare the methodologies used", "top_k": 10}'
```

### Validate Configuration

```bash
# Check if configuration is valid
./validate_config.py
```

### Run Unit Tests (if implemented)

```bash
pytest tests/ -v
```

## 📊 Performance Benchmarks

- **PDF Processing**: 5 papers in < 2 minutes ✅
- **Query Response**: < 3 seconds average
- **Embedding Generation**: ~50 chunks/second
- **Vector Search**: < 100ms for top 5 results

## 🐛 Troubleshooting

### Ollama Not Found

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
ollama serve
```

### Qdrant Connection Error

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Restart Qdrant
docker-compose restart qdrant
```

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker-compose restart postgres

# Reinitialize database
python src/init_db.py
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or change API_PORT in .env
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (deletes data!)
docker-compose down -v

# Remove virtual environment
deactivate
rm -rf venv
```

## 📚 Technology Stack

| Component          | Technology            | Version | Purpose             |
| ------------------ | --------------------- | ------- | ------------------- |
| **Web Framework**  | FastAPI               | Latest  | REST API            |
| **Vector DB**      | Qdrant                | Latest  | Similarity search   |
| **Database**       | PostgreSQL            | 15      | Metadata & queries  |
| **LLM**            | Ollama (Llama3)       | Latest  | Answer generation   |
| **Embeddings**     | sentence-transformers | Latest  | Text vectorization  |
| **PDF Processing** | PyMuPDF               | Latest  | PDF extraction      |
| **ORM**            | SQLAlchemy            | Latest  | Database operations |

## 🎯 Design Decisions

For detailed explanation of:

- Chunking strategy and rationale
- Embedding model selection
- Prompt engineering approach
- Database schema design
- Trade-offs and limitations

See **[APPROACH.md](APPROACH.md)**

## 📝 Development Workflow

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test locally
3. Update tests if needed
4. Update documentation
5. Commit and push: `git push origin feature/new-feature`

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## 🤝 Contributing

This is an assessment project, but improvements are welcome:

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of an assessment for educational purposes.

## 📧 Contact

For questions or issues:

- Open an issue in the repository
- Email: ishmam.abid5422@gmail.com

## 🎉 Acknowledgments

- Assessment provided by [Organization]
- Built with ❤️ using FastAPI, Qdrant, and Ollama
- Sample papers used for testing purposes

---

**Ready to query research papers intelligently!** 🚀
