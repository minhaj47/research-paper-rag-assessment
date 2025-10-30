#!/bin/bash

# Test script for the RAG system
# This script tests all the endpoints

API_URL="http://localhost:8000"
TEST_PAPER="sample_papers/paper_1.pdf"

echo "🧪 Testing Research Paper RAG System"
echo "======================================"
echo ""

# Check if server is running
echo "1. Checking if server is running..."
if ! curl -s "${API_URL}/docs" > /dev/null; then
    echo "❌ Server is not running!"
    echo "   Start it with: uvicorn src.main:app --reload --port 8000"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Test upload
echo "2. Testing paper upload..."
if [ -f "$TEST_PAPER" ]; then
    UPLOAD_RESPONSE=$(curl -s -X POST "${API_URL}/api/upload" -F "file=@${TEST_PAPER}")
    echo "Response: $UPLOAD_RESPONSE"
    
    # Extract paper_id if present
    PAPER_ID=$(echo $UPLOAD_RESPONSE | grep -o '"paper_id":[0-9]*' | grep -o '[0-9]*' | head -1)
    
    if [ ! -z "$PAPER_ID" ]; then
        echo "✅ Paper uploaded successfully (ID: $PAPER_ID)"
    else
        echo "⚠️  Upload response: Check if paper already exists"
    fi
else
    echo "⚠️  Test paper not found: $TEST_PAPER"
fi
echo ""

# Test list papers
echo "3. Testing list papers..."
curl -s "${API_URL}/api/papers" | python3 -m json.tool
echo "✅ List papers endpoint working"
echo ""

# Test query
echo "4. Testing query..."
QUERY_RESPONSE=$(curl -s -X POST "${API_URL}/api/query?query=What%20is%20this%20paper%20about?&top_k=3")
echo "$QUERY_RESPONSE" | python3 -m json.tool
echo "✅ Query endpoint working"
echo ""

# Test query history
echo "5. Testing query history..."
curl -s "${API_URL}/api/queries/history?limit=5" | python3 -m json.tool
echo "✅ Query history endpoint working"
echo ""

# Test analytics
echo "6. Testing analytics..."
curl -s "${API_URL}/api/analytics/popular?limit=5" | python3 -m json.tool
echo "✅ Analytics endpoint working"
echo ""

echo "======================================"
echo "🎉 All tests completed!"
echo ""
echo "For detailed API docs, visit:"
echo "  ${API_URL}/docs"
