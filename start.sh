#!/bin/bash

# One-command Docker setup for Research Paper RAG System
# This script starts everything with Docker Compose

set -e

echo "🚀 Research Paper RAG System - Docker Setup"
echo "============================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    echo "   Please install Docker Compose"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running!"
    echo "   Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker daemon is running"
echo ""

# Ask if user wants to rebuild
echo "Do you want to rebuild the containers? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    BUILD_FLAG="--build"
else
    BUILD_FLAG=""
fi

echo ""
echo "🐳 Starting services with Docker Compose..."
echo ""

# Start Docker Compose
if [ -n "$BUILD_FLAG" ]; then
    docker-compose up $BUILD_FLAG -d
else
    docker-compose up -d
fi

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "============================================"
echo "✅ Setup Complete!"
echo "============================================"
echo ""
echo "📡 Services Running:"
echo "   • API Server:  http://localhost:8000"
echo "   • API Docs:    http://localhost:8000/docs"
echo "   • Qdrant:      http://localhost:6333"
echo "   • PostgreSQL:  localhost:5432"
echo ""
echo "🧪 Quick Test:"
echo "   # Upload a paper"
echo "   curl -X POST 'http://localhost:8000/api/upload' \\"
echo "     -F 'file=@sample_papers/paper_1.pdf'"
echo ""
echo "   # List papers"
echo "   curl 'http://localhost:8000/api/papers'"
echo ""
echo "📋 View Logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop Services:"
echo "   docker-compose down"
echo ""
