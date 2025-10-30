#!/bin/bash

# Quick Start Script for Research Paper RAG System
# This script sets up and runs the entire system

set -e  # Exit on error

echo "🚀 Starting Research Paper RAG System Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Docker
echo "📦 Step 1: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo -e "${GREEN}✅ Docker is installed${NC}"
echo ""

# Step 2: Start Docker Services
echo "🐳 Step 2: Starting Docker services (Qdrant & PostgreSQL)..."
docker-compose up -d
echo -e "${GREEN}✅ Docker services started${NC}"
echo ""

# Wait for PostgreSQL to be healthy
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
echo ""

# Step 3: Create .env file
echo "⚙️  Step 3: Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists, skipping${NC}"
fi
echo ""

# Step 4: Check Python environment
echo "🐍 Step 4: Checking Python environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi
echo ""

# Step 5: Activate and install dependencies
echo "📚 Step 5: Installing Python dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 6: Initialize database
echo "💾 Step 6: Initializing database..."
python src/init_db.py
echo ""

# Step 7: Check Ollama
echo "🤖 Step 7: Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama is not installed${NC}"
    echo "   Install it from: https://ollama.ai"
    echo "   Then run: ollama pull llama3:latest"
else
    echo -e "${GREEN}✅ Ollama is installed${NC}"
    
    # Check if model is pulled
    if ollama list | grep -q "llama3"; then
        echo -e "${GREEN}✅ llama3 model is available${NC}"
    else
        echo -e "${YELLOW}⚠️  llama3 model not found. Pulling it now...${NC}"
        ollama pull llama3:latest
        echo -e "${GREEN}✅ llama3 model pulled${NC}"
    fi
fi
echo ""

# Final summary
echo "============================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "============================================"
echo ""
echo "Services running:"
echo "  • Qdrant:     http://localhost:6333"
echo "  • PostgreSQL: localhost:5432"
echo ""
echo "Next steps:"
echo "  1. Start the API server:"
echo "     uvicorn src.main:app --reload --port 8000"
echo ""
echo "  2. Open another terminal and test:"
echo "     curl -X POST 'http://localhost:8000/api/upload' \\"
echo "       -F 'file=@sample_papers/paper_1.pdf'"
echo ""
echo "  3. View API documentation:"
echo "     http://localhost:8000/docs"
echo ""
echo "For more details, see README.md"
echo ""
