# 🐳 Docker Setup Guide

## Prerequisites

1. **Docker & Docker Compose** installed
2. **Ollama running locally** on your macOS:

   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/version

   # If not running, start it
   ollama serve
   ```

3. **Pull your preferred model**:
   ```bash
   ollama pull llama3
   ```

## 🚀 Quick Start (One Command)

```bash
docker-compose up --build
```

That's it! This will:

- ✅ Start Qdrant (vector database)
- ✅ Start PostgreSQL (metadata database)
- ✅ Build and start the FastAPI application
- ✅ Initialize the database schema
- ✅ Connect to your local Ollama instance

## 🔍 What's Running

After starting, you'll have:

- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **PostgreSQL**: localhost:5432
- **Ollama**: http://localhost:11434 (on your Mac, not in Docker)

## 📝 Usage Commands

### Start everything

```bash
docker-compose up --build
```

### Start in background (detached mode)

```bash
docker-compose up -d --build
```

### View logs

```bash
docker-compose logs -f api
```

### Stop everything

```bash
docker-compose down
```

### Stop and remove volumes (clean slate)

```bash
docker-compose down -v
```

### Rebuild after code changes

```bash
docker-compose up --build
```

## 🧪 Testing the Setup

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Upload a Paper

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_papers/paper_1.pdf"
```

### 3. Query the System

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main contribution of this paper?", "top_k": 5}'
```

## 🔧 Configuration

Environment variables are set in `.env` file:

```bash
# Database credentials
POSTGRES_USER=raguser
POSTGRES_PASSWORD=ragpass
POSTGRES_DB=ragdb

# Ollama model
OLLAMA_MODEL=llama3:latest
```

The `docker-compose.yml` automatically:

- Uses `host.docker.internal` to connect to your local Ollama
- Maps volumes for persistent data
- Sets up health checks for all services

## 🐛 Troubleshooting

### Can't connect to Ollama

```bash
# Test from your Mac
curl http://localhost:11434/api/version

# Test from Docker container
docker exec -it rag_api curl http://host.docker.internal:11434/api/version
```

### Database connection issues

```bash
# Check if PostgreSQL is ready
docker-compose logs postgres

# Restart services
docker-compose restart postgres api
```

### Clear everything and start fresh

```bash
docker-compose down -v
docker system prune -a --volumes -f
docker-compose up --build
```

### Check service status

```bash
docker-compose ps
```

## 📊 Architecture

```
┌─────────────────┐
│   Your MacOS    │
│                 │
│  Ollama:11434   │ ◄──────────┐
└─────────────────┘            │
                               │
┌──────────────────────────────┼──────────────┐
│          Docker Network      │              │
│                              │              │
│  ┌──────────┐  ┌──────────┐ │ ┌─────────┐ │
│  │ Qdrant   │  │Postgres  │ │ │   API   │ │
│  │  :6333   │  │  :5432   │ │ │  :8000  │ │
│  └──────────┘  └──────────┘ │ └─────────┘ │
│                              │      │       │
│                              └──────┘       │
│                      host.docker.internal  │
└────────────────────────────────────────────┘
```

## 🎯 What Changed from Original Setup

### ❌ Removed

- Ollama container (using your local installation instead)
- Unnecessary shell scripts
- Complex startup sequences
- gcc/g++ from Dockerfile (not needed)
- .env.example copying in Dockerfile

### ✅ Added

- Health endpoint in API
- `host.docker.internal` for Mac Ollama access
- Proper service dependencies
- Restart policies
- Clean .dockerignore
- Better logging

## 🔐 Production Notes

For production deployment:

1. Change default passwords in `.env`
2. Use proper secrets management
3. Set `ENVIRONMENT=production`
4. Consider using managed services for databases
5. Use a reverse proxy (nginx) in front of the API

## 📚 Next Steps

1. Upload your research papers
2. Test queries
3. Monitor logs: `docker-compose logs -f`
4. Scale if needed: `docker-compose up --scale api=3`
