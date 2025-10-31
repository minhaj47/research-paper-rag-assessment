# 🎓 Research Paper RAG System

A production-ready Retrieval-Augmented Generation (RAG) service for querying academic research papers using vector search and LLMs.

## 🚀 Quick Start (One Command)

**Prerequisites:**

- Docker and Docker Compose installed
- Ollama running on your host machine with `llama3` model

```bash
# 1. Install Ollama (one-time setup)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3

# 2. Run Ollama server
ollama run llama3
# This will start Ollama at http://localhost:11434/
# Keep this terminal running

# 3. In a new terminal, clone and run the project
git clone https://github.com/minhaj47/research-paper-rag-assessment.git
cd research-paper-rag-assessment
git checkout submission/minhaj
docker compose up --build
```

That's it! The system will be ready:

- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000

**Quick test:**

Option 1: **Web Interface** (Recommended)

- Open http://localhost:3000 in your browser
- Upload PDFs via drag & drop
- Ask questions and see real-time streaming answers

Option 2: **API (curl)**

```bash
curl -X POST -F "files=@sample_papers/paper_1.pdf" http://localhost:8000/api/upload
```

**⚠️ Port Conflict?** If you see `Error: bind: address already in use`:

```bash
# Find and kill the process using port 3000
sudo kill -9 $(lsof -t -i:3000)

# Or for port 8000
sudo kill -9 $(lsof -t -i:8000)
```

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Setup Instructions](#-setup-instructions)
- [API Documentation](#-api-documentation)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### Core Features

- ✅ **PDF Upload & Processing** - Multi-file upload with section-aware extraction
- ✅ **Intelligent Query System** - RAG pipeline with citations and confidence scores
- ✅ **Paper Management** - CRUD operations for managing uploaded papers
- ✅ **Vector Search** - Semantic search using Qdrant vector database
- ✅ **Citation Extraction** - Automatic citation mapping with source tracking
- ✅ **Confidence Scoring** - AI-generated confidence levels for answers
- ✅ **Query History & Analytics** - Track queries and view popular topics
- 🎨 **Modern Web UI** - Next.js/React frontend with beautiful interface

### Technical Features

- 🐳 **Fully Dockerized** - Backend, frontend, and databases all containerized
- 🔄 **Live Reload** - Development mode with auto-reload
- �️ **PostgreSQL Storage** - Persistent metadata storage
- 🔍 **Qdrant Vector DB** - Fast similarity search with HNSW indexing
- 🤖 **Ollama Integration** - Local LLM for answer generation
- 📊 **Structured Responses** - JSON API with proper error handling
- 🎨 **Modern Web UI** - Beautiful, responsive Next.js app with SSE streaming
- ⚡ **Performance Optimized** - Query caching, batch operations, score thresholding
- 🎯 **Advanced Re-ranking** - Cross-encoder re-ranking for improved relevance (~10-15% better results)

---

## 🏗️ Architecture

![System Architecture](architecture.png)

### Key Components

#### Frontend (Port 3000)

- **Next.js Application**: Modern React framework with SSE streaming
- **File Upload**: Drag & drop interface for PDF uploads
- **Query Interface**: Real-time streaming answers with citations
- **Paper Management**: View, delete, and analyze uploaded papers

#### Backend API (Port 8000)

- **FastAPI Framework**: High-performance async API with auto-documentation
- **Document Ingestion**: PDF extraction → Chunking → Embedding → Storage
- **RAG Pipeline**: Two-stage retrieval (Bi-encoder + Cross-encoder)

#### Storage

- **PostgreSQL**: Metadata (papers, queries, history)
- **Qdrant**: 384-dimensional vector embeddings with COSINE similarity

#### External Services

- **Ollama**: Local LLM inference with llama3 model

### Data Flow

**Upload Flow** (Steps 1-4):

1. User uploads PDF via web interface
2. PDF text extraction with section detection
3. Text chunking with overlap for context preservation
4. Embedding generation + storage in Qdrant & PostgreSQL

**Query Flow** (Steps 1-12):

1. User submits question
2. Query embedding generation
3. Retrieve top_k × 2 candidates (bi-encoder, fast)
4. Re-rank with cross-encoder (slow, accurate)
5. Fetch paper metadata
6. Build LLM prompt with top-K contexts
7. Stream response from Ollama
8. Parse and extract citations
9. Save query history
10. Return answer with confidence scores

---

## 🛠️ Setup Instructions

### Prerequisites

1. **Docker & Docker Compose**

   ```bash
   # Check if installed
   docker --version
   docker-compose --version

   # Install if needed: https://docs.docker.com/get-docker/
   ```

2. **Ollama (for LLM)**

   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull the model
   ollama pull llama3

   # Run Ollama server (keep this running)
   ollama run llama3
   # Server will be available at http://localhost:11434/

   # In another terminal, verify it's running
   curl http://localhost:11434/api/tags
   ```

### Installation

#### With User Permissions (Linux/macOS)

If you want files created by the container to match your user (avoids permission issues):

```bash
# Set your user ID
export UID=$(id -u)
export GID=$(id -g)

# Start services
docker-compose up --build
```

The script adds:

- ✅ Prerequisite validation (Docker, Ollama)
- ✅ Auto-detection of OS and user
- ✅ Service health checks
- ✅ Pretty output with status messages

### Verify Installation

```bash
# Check all services are running
docker-compose ps

# Test API health
curl http://localhost:8000/docs

# Test Qdrant
curl http://localhost:6333/collections
```

---

## 📡 API Documentation

### Base URL

```
http://localhost:8000
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### 1. Upload Papers

```http
POST /api/upload
Content-Type: multipart/form-data

files: (multiple PDF files)
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "files=@sample_papers/paper_1.pdf" \
  -F "files=@sample_papers/paper_2.pdf"
```

**Response:**

```json
{
  "status": "success",
  "filename": "paper_1.pdf",
  "paper_id": 1,
  "metadata": {
    "title": "Sustainability in Blockchain",
    "author": "Hani Alshahrani et al.",
    "page_count": 24
  },
  "sections": {
    "Abstract": {
      "chunk_count": 3,
      "start_page": 1
    },
    "Introduction": {
      "chunk_count": 15,
      "start_page": 2
    }
  },
  "total_chunks": 119,
  "content_type": "application/pdf",
  "file_size": 3470416
}
```

#### 2. Query Papers (RAG)

```http
POST /api/query
Content-Type: application/json

Parameters:
- query (string, required): Your question
- top_k (integer, optional): Number of results (default: 5)
- paper_ids (array, optional): Filter by specific paper IDs
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/query?query=What%20methodology%20was%20used?&top_k=5"
```

**Response:**

```json
{
  "answer": "Based on the provided context...",
  "citations": [
    {
      "paper_title": "Sustainability in Blockchain",
      "section": "Introduction",
      "page": 8,
      "relevance_score": 0.77,
      "text": "excerpt from the paper..."
    }
  ],
  "sources_used": ["paper_1.pdf"],
  "confidence": 0.54,
  "response_time": 2.35
}
```

#### 3. Paper Management

```bash
GET /api/papers              # List all papers
GET /api/papers/{id}         # Get paper details
DELETE /api/papers/{id}      # Delete paper
GET /api/papers/{id}/stats   # Get chunk statistics
GET /api/queries/history     # Query history
GET /api/analytics/popular   # Popular queries
```

**Example: List Papers**

```bash
curl http://localhost:8000/api/papers
```

**Response:**

```json
{
  "total": 5,
  "papers": [
    {
      "id": 1,
      "filename": "paper_1.pdf",
      "title": "Sustainability in Blockchain",
      "author": "Hani Alshahrani et al.",
      "page_count": 24,
      "total_chunks": 119,
      "upload_date": "2025-10-31T10:30:00"
    }
  ]
}
```

**📖 Interactive API Docs:** http://localhost:8000/docs

---

## 💡 Usage Examples

### Example 1: Python Client

```python
import requests

# Upload a paper
files = [('files', open('sample_papers/paper_1.pdf', 'rb'))]
upload_result = requests.post('http://localhost:8000/api/upload', files=files).json()
print(f"Uploaded: {upload_result['filename']}, Paper ID: {upload_result['paper_id']}")

# Query the system
query_params = {"query": "What is blockchain?", "top_k": 5}
result = requests.post('http://localhost:8000/api/query', params=query_params).json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
```

## 📁 Project Structure

```
research-paper-rag-assessment/
├── src/                             # Backend Python code
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # API endpoint definitions with SSE streaming
│   ├── models/
│   │   ├── __init__.py
│   │   └── db.py                    # SQLAlchemy models (papers, queries)
│   └── services/
│       ├── __init__.py
│       ├── pdf_processor.py         # PDF extraction logic
│       ├── embedding_service.py     # Sentence transformers with caching
│       ├── qdrant_client.py         # Qdrant client with HNSW indexing
│       ├── rag_pipeline.py          # RAG query pipeline with cross-encoder
│       ├── ollama_client.py         # Ollama LLM client with streaming
│       └── chunking.py              # Text chunking strategies
├── frontend/                        # Next.js web interface
│   ├── app/                         # Next.js App Router
│   ├── components/                  # React components
│   │   ├── QueryInterface.tsx       # Query UI with SSE streaming
│   │   ├── PaperList.tsx           # Paper management
│   │   └── FileUpload.tsx          # Drag & drop upload
│   ├── Dockerfile                   # Frontend container (multi-stage)
│   ├── package.json                 # Node.js dependencies
│   ├── next.config.js               # Next.js configuration
│   └── tailwind.config.js           # Tailwind CSS configuration
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests (45 tests)
│   │   ├── test_chunking.py         # Chunking logic tests
│   │   ├── test_pdf_processor.py    # PDF extraction tests
│   │   ├── test_rag_pipeline.py     # RAG pipeline tests
│   │   ├── test_embedding_service.py # Embedding tests
│   │   └── test_reranking.py        # Re-ranking tests
│   ├── test_query_api.sh            # API endpoint tests
│   ├── test_query_examples.py       # Query flow tests
│   └── test_paper_management.py     # CRUD operation tests
├── sample_papers/                   # Test PDF files
├── uploads/                         # Uploaded files (auto-created)
├── logs/                            # Application logs
├── vector_store/                    # Qdrant vector storage
├── docker-compose.yml               # All services: frontend, API, DB, Qdrant
├── Dockerfile                       # Backend API container
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── APPROACH.md                      # Technical design decisions
├── test_queries.json                # Sample test queries
└── README.md                        # This file
```

---

### Docker Services

The `docker-compose.yml` defines four services:

1. **Frontend (Next.js)** - Port 3000 - Modern web interface
2. **API (FastAPI)** - Port 8000 - Backend REST API
3. **PostgreSQL** - Port 5432 - Paper metadata storage
4. **Qdrant** - Port 6333 - Vector database

All services use persistent volumes to preserve data across restarts.

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Ollama Connection Refused

**Symptom:** Queries return empty answers or "Connection refused" errors

**Solution:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama server (keep this terminal open)
ollama run llama3

# If model is missing, pull it first
ollama pull llama3

# Verify the server is accessible
curl http://localhost:11434/api/generate -d '{"model":"llama3","prompt":"test"}'
```

**Note:** Ollama must be running on the host machine at `http://localhost:11434/` for the Docker containers to access it.

If the above steps don't help, check container logs via `docker-compose logs api`.

#### 2. Permission Denied on uploads/ or logs/ Directory

**Symptom:** Cannot write files to uploads/ or logs/

**Solution:**

```bash
# Fix ownership (one-time)
sudo chown -R $USER:$USER uploads/ logs/ vector_store/

# Rebuild containers
docker-compose down
docker-compose up --build
```

#### 3. Port 3000 Already in Use (Frontend Conflict)

**Symptom:** `Error: bind: address already in use` when starting frontend container

**Cause:** Another service is using port 3000 (common for Next.js/React dev servers)

**Solution:**

```bash
# Check what's using port 3000
lsof -i :3000

# Kill the process
sudo kill -9 $(lsof -t -i:3000)

# Then start Docker
docker compose up --build
```

#### 4. Port 8000 Already in Use (Backend Conflict)

**Symptom:** Backend API fails to start

**Solution:**

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Stop conflicting service
sudo kill -9 $(lsof -t -i:8000)

# Or stop all containers and restart
docker compose down
docker compose up --build
```

#### 5. Container Fails to Start

**Solution:**

```bash
# Check logs
docker compose logs api
docker compose logs frontend

# Rebuild from scratch
docker compose down -v
docker system prune -f
./setup.sh
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow API logs
docker-compose logs -f api

# Check container status
docker-compose ps

# Enter API container
docker exec -it rag_api bash
```

---

## 🎨 Web Interface

**Frontend:** http://localhost:3000

**Features:**

- 📤 Drag & drop PDF upload
- 🔍 Real-time query interface
- 📚 Paper management with stats
- 📊 Query history & analytics

**Local Dev:**

```bash
cd frontend && npm install && npm run dev
```

---

## 🧪 Testing

```bash
# Test API endpoints
curl http://localhost:8000/health

# Upload a sample paper
curl -X POST -F "files=@sample_papers/paper_1.pdf" http://localhost:8000/api/upload

# Query the system
curl "http://localhost:8000/api/query?query=What%20is%20blockchain?&top_k=5"
```

---

## 🔧 Development

```bash
docker-compose up                  # Start with live reload
docker-compose logs -f api         # View logs
docker-compose down                # Stop (data persists)
docker-compose down -v             # Stop + clean volumes
```

---

## 🙏 Acknowledgments

- **Qdrant** - Vector database
- **Ollama** - Local LLM inference
- **FastAPI** - Web framework
- **sentence-transformers** - Embedding models

---

**Built with ❤️ for UpScaleBD**
