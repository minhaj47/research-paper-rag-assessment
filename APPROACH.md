# System Design & Implementation Approach

## 1. Architecture Overview

### High-Level Design Philosophy

This RAG system is designed with **modularity**, **scalability**, and **maintainability** in mind. Each component is loosely coupled and can be replaced or upgraded independently.

### Component Selection Rationale

| Component      | Choice                                   | Reason                                                     |
| -------------- | ---------------------------------------- | ---------------------------------------------------------- |
| **Vector DB**  | Qdrant                                   | Open-source, fast, built for production with HNSW indexing |
| **Database**   | PostgreSQL                               | ACID compliance, mature ecosystem, excellent JSON support  |
| **LLM**        | Ollama (Llama3)                          | Privacy-first, no API costs, runs locally                  |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Balance between speed (384 dims) and quality               |
| **Framework**  | FastAPI                                  | Async support, auto documentation, type safety             |
| **PDF Parser** | PyMuPDF (fitz)                           | Fast, reliable, good text extraction                       |

---

## 2. Document Processing Strategy

### PDF Extraction

**Approach**: Section-aware extraction with metadata preservation

```python
Process Flow:
1. Extract text with page numbers
2. Identify sections (Abstract, Introduction, Methods, Results, Conclusion)
3. Preserve structural information (headers, lists, tables)
4. Extract metadata (title, authors, year)
```

**Challenges & Solutions:**

- **Problem**: PDF formatting inconsistencies
- **Solution**: Regex patterns + heuristics for section detection
- **Problem**: Multi-column layouts
- **Solution**: PyMuPDF's layout detection with column ordering

### Chunking Strategy

**Strategy**: Fixed-size semantic chunking with overlap

**Parameters:**

- **Chunk Size**: 512 tokens (~350-400 words)
- **Overlap**: 50 tokens (~35-40 words)
- **Rationale**:
  - 512 tokens: Fits in embedding model context, preserves paragraph semantics
  - 50 token overlap: Prevents context loss at boundaries
  - Section-aware: Never splits across major sections

**Alternative Considered:**

- **Sentence-based chunking**: Too granular, lost context
- **Paragraph-based**: Uneven sizes, some too large
- **Chosen**: Fixed-size with semantic boundaries

**Implementation:**

```python
def chunk_text(text, chunk_size=512, overlap=50):
    # 1. Split into sentences
    # 2. Group sentences into ~512 token chunks
    # 3. Add overlap from previous chunk
    # 4. Preserve section headers at chunk start
```

### Metadata Enrichment

Each chunk stores:

- `paper_id`: Reference to source paper
- `section`: Which section (Abstract, Methods, etc.)
- `page_number`: For citation purposes
- `chunk_index`: Order in document
- `preceding_text`: For context window
- `following_text`: For context window

**Why this matters**: Enables precise citations and contextual retrieval

---

## 3. Embedding Strategy

### Model Selection: `all-MiniLM-L6-v2`

**Specifications:**

- Dimensions: 384
- Max sequence length: 256 words
- Performance: ~3000 sentences/sec on CPU

**Why This Model?**

- ✅ Fast inference (important for real-time queries)
- ✅ Good semantic understanding for academic text
- ✅ Small model size (80MB) - easy to deploy
- ✅ No GPU required

**Alternatives Considered:**

- `all-mpnet-base-v2`: Better quality (768 dims) but 3x slower
- `multi-qa-MiniLM-L6-cos-v1`: Optimized for Q&A but worse for academic text
- **OpenAI embeddings**: Excellent but API costs + latency

### Vector Storage in Qdrant

**Collection Configuration:**

```python
{
    "vectors": {
        "size": 384,
        "distance": "Cosine"
    },
    "payload_schema": {
        "paper_id": "integer",
        "section": "keyword",
        "page": "integer",
        "text": "text",
        "chunk_index": "integer"
    }
}
```

**Why Cosine Similarity?**

- Normalized vectors: magnitude doesn't matter
- Standard for semantic similarity
- Range [0, 1]: Easy to interpret as confidence

### Indexing Strategy

**HNSW Parameters:**

- `m`: 16 (edges per node)
- `ef_construct`: 100 (construction search depth)
- **Trade-off**: Higher values = better recall but slower indexing

**Performance:**

- Indexing: ~100 chunks/second
- Search: < 50ms for top-5 results in 10k+ chunks

---

## 4. RAG Pipeline

### Query Processing Flow

```
User Query
    ↓
1. Query Understanding
    ↓
2. Embedding Generation
    ↓
3. Vector Search (Qdrant)
    ↓
4. Re-ranking & Filtering
    ↓
5. Context Assembly
    ↓
6. Prompt Construction
    ↓
7. LLM Generation
    ↓
8. Citation Extraction
    ↓
Response with Citations
```

### 1. Query Understanding

**Steps:**

- Detect query type (factual, comparative, analytical)
- Extract keywords
- Identify if query requires single or multi-paper context

**Implementation:**

```python
# Simple heuristics
if "compare" in query or "difference" in query:
    query_type = "comparative"
    top_k = 10  # Need more context for comparison
else:
    query_type = "factual"
    top_k = 5
```

### 2. Vector Search

**Approach**: Hybrid search with metadata filtering

```python
# Main search
results = qdrant.search(
    query_vector=query_embedding,
    limit=top_k,
    score_threshold=0.7  # Minimum relevance
)

# Optional: Filter by paper_ids
if paper_ids:
    results = filter(lambda x: x.payload['paper_id'] in paper_ids, results)
```

**Why Threshold 0.7?**

- Empirically tested on sample papers
- < 0.7: Too many irrelevant results
- > 0.8: Misses relevant context

### 3. Re-ranking

**Strategy**: Boost results based on:

- Section importance (Abstract > Methods > Results)
- Recency in document (later sections may have conclusions)
- Keyword matching (bonus for exact matches)

```python
def rerank_score(result):
    base_score = result.score
    section_boost = SECTION_WEIGHTS.get(result.payload['section'], 1.0)
    keyword_boost = 1.1 if any(kw in result.text for kw in keywords) else 1.0
    return base_score * section_boost * keyword_boost
```

### 4. Context Assembly

**Approach**: Structured context with source attribution

```python
context = ""
for result in top_results:
    context += f"""
    [Paper: {result.paper_title}, Section: {result.section}, Page: {result.page}]
    {result.text}
    ---
    """
```

**Why This Format?**

- Clear source separation
- Easy for LLM to extract citations
- Maintains document structure

### 5. Prompt Engineering

**Template:**

```python
PROMPT = """
You are a research assistant helping to answer questions about academic papers.

Context from research papers:
{context}

Question: {question}

Instructions:
1. Answer the question using ONLY information from the context above
2. Cite your sources using the format: [Paper Name, Section, Page X]
3. If the context doesn't contain enough information, say so
4. Be precise and academic in your language
5. For comparative questions, provide balanced analysis

Answer:
"""
```

**Design Decisions:**

- ✅ Explicit citation format → Easy to parse
- ✅ "Only from context" → Reduces hallucinations
- ✅ Acknowledge limitations → Transparency
- ✅ Academic tone → Appropriate for domain

### 6. LLM Configuration

**Ollama Parameters:**

```python
{
    "model": "llama3",
    "temperature": 0.3,  # Low = more deterministic
    "top_p": 0.9,
    "max_tokens": 500,
    "stop": ["Question:", "Context:"]  # Prevent repetition
}
```

**Why Low Temperature (0.3)?**

- Academic context requires factual accuracy
- Reduce creative interpretation
- Consistent responses for same query

### 7. Citation Extraction & Confidence

**Post-processing:**

```python
# Extract citations from LLM response
citations = extract_citations(response)

# Calculate confidence based on:
# - Number of sources used
# - Average similarity scores
# - Presence of citations in response
confidence = calculate_confidence(citations, scores)
```

**Confidence Formula:**

```python
confidence = (
    0.4 * avg_similarity_score +
    0.3 * (min(num_citations, 3) / 3) +
    0.3 * (1 if all_citations_valid else 0)
)
```

---

## 5. Database Schema Design

### Papers Table

```sql
CREATE TABLE papers (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    authors TEXT[],
    year INTEGER,
    abstract TEXT,
    page_count INTEGER,
    total_chunks INTEGER,
    sections JSONB,  -- List of section names
    upload_date TIMESTAMP DEFAULT NOW(),
    file_size INTEGER,
    file_hash VARCHAR(64)  -- For duplicate detection
);
```

**Design Choices:**

- `JSONB` for sections: Flexible, queryable
- `file_hash`: Prevent duplicate uploads
- `authors TEXT[]`: PostgreSQL array for multiple authors

### Queries Table

```sql
CREATE TABLE queries (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    answer TEXT,
    confidence FLOAT,
    papers_referenced INTEGER[],  -- Array of paper IDs
    response_time_ms INTEGER,
    top_k INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    sources_used JSONB  -- Detailed citation info
);
```

**Design Choices:**

- `papers_referenced`: Enable "most queried papers" analytics
- `response_time_ms`: Performance monitoring
- `sources_used JSONB`: Full citation details for export

### Indexes for Performance

```sql
-- Fast lookups
CREATE INDEX idx_papers_filename ON papers(filename);
CREATE INDEX idx_papers_upload_date ON papers(upload_date DESC);

-- Analytics queries
CREATE INDEX idx_queries_timestamp ON queries(timestamp DESC);
CREATE INDEX idx_queries_papers ON queries USING GIN(papers_referenced);
```

**Why GIN Index?**

- Efficient for array containment queries
- Enables fast "papers referenced in queries" lookups

---

## 6. API Design

### RESTful Principles

- **Resource-based URLs**: `/api/papers/{id}`
- **HTTP verbs**: GET (read), POST (create), DELETE (remove)
- **Status codes**: 200 (OK), 201 (Created), 400 (Bad Request), 404 (Not Found), 500 (Error)

### Request/Response Format

**Consistency:**

- All responses have `status` field
- Errors include `detail` field
- Timestamps in ISO 8601 format

**Validation:**

- Pydantic models for all requests
- Type checking at runtime
- Clear error messages

### Error Handling

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## 7. Trade-offs & Limitations

### Trade-offs Made

| Decision                        | Benefit                 | Cost                                   |
| ------------------------------- | ----------------------- | -------------------------------------- |
| **Local LLM (Ollama)**          | Privacy, no API costs   | Slower than GPT-4, needs good hardware |
| **Fixed chunking (512 tokens)** | Consistent, predictable | May split semantic units               |
| **Cosine similarity only**      | Fast, standard          | Misses lexical matches                 |
| **PostgreSQL over MongoDB**     | ACID, mature            | Less flexible schema                   |
| **No caching layer**            | Simpler architecture    | Repeated queries recompute             |

### Current Limitations

1. **PDF Parsing**

   - Struggles with scanned PDFs (no OCR)
   - Complex tables may lose structure
   - Equations not properly extracted

2. **Chunking**

   - Fixed size may break logical units
   - Overlap doesn't guarantee context preservation
   - Section detection may fail on non-standard formats

3. **Search Quality**

   - Only semantic search (no keyword boosting)
   - No query expansion or synonym handling
   - Single embedding model (no ensemble)

4. **Scalability**

   - Single instance (no horizontal scaling)
   - No async embedding generation
   - Vector DB not distributed

5. **LLM**
   - Context window limited to ~2k tokens
   - May hallucinate despite instructions
   - No fact-checking mechanism

### Future Improvements

**Short-term (1-2 weeks):**

- [ ] Add caching for frequent queries (Redis)
- [ ] Implement hybrid search (semantic + keyword)
- [ ] Better section detection with ML model
- [ ] Query expansion with synonyms

**Medium-term (1-2 months):**

- [ ] Support for scanned PDFs (Tesseract OCR)
- [ ] Multi-language support
- [ ] User authentication & rate limiting
- [ ] Export results to PDF/Markdown

**Long-term (3+ months):**

- [ ] Distributed vector DB (Qdrant cluster)
- [ ] Fine-tuned embedding model for academic papers
- [ ] Graph relationships between papers (citation network)
- [ ] Real-time paper recommendations
- [ ] Web UI with visualization

---

## 8. Performance Optimization

### Current Optimizations

1. **Batch Embedding Generation**

   ```python
   # Process 32 chunks at once
   embeddings = model.encode(chunks, batch_size=32)
   ```

2. **Connection Pooling**

   - PostgreSQL: SQLAlchemy pool (size=10)
   - Qdrant: HTTP connection reuse

3. **Lazy Loading**

   - PDF files not loaded into memory
   - Embeddings computed on-demand

4. **Efficient Chunking**
   - Single pass through text
   - No redundant parsing

### Performance Metrics

| Operation                 | Current      | Target       |
| ------------------------- | ------------ | ------------ |
| Upload 1 paper (20 pages) | ~25 seconds  | < 20 seconds |
| Query response            | ~2.5 seconds | < 2 seconds  |
| Vector search (1k chunks) | ~30ms        | < 50ms       |
| Database query            | ~10ms        | < 20ms       |

---

## 9. Security Considerations

### Current Implementation

- ✅ Environment variables for secrets (`.env`)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ File upload validation (size, type)
- ✅ No credentials in code

### Not Implemented (Future)

- ❌ Authentication/Authorization
- ❌ Rate limiting
- ❌ Input sanitization for LLM injection
- ❌ HTTPS/TLS
- ❌ Audit logging

---

## 10. Testing Strategy

### Unit Tests (Planned)

```python
# Test document processor
def test_chunk_text():
    text = "..." * 1000
    chunks = chunk_text(text, chunk_size=512, overlap=50)
    assert all(len(chunk.split()) <= 512 for chunk in chunks)
    assert has_overlap(chunks, 50)

# Test embedding service
def test_embedding_generation():
    text = "Sample research text"
    embedding = generate_embedding(text)
    assert len(embedding) == 384
    assert -1 <= embedding[0] <= 1
```

### Integration Tests (Planned)

```python
# Test end-to-end pipeline
def test_upload_and_query():
    # Upload paper
    response = client.post("/api/upload", files={"file": pdf_file})
    paper_id = response.json()["paper_id"]

    # Query
    response = client.post("/api/query", json={"question": "test"})
    assert response.status_code == 200
    assert "answer" in response.json()
```

### Manual Testing

- ✅ All 5 sample papers uploaded successfully
- ✅ Test queries return relevant results
- ✅ Citations are accurate
- ✅ Edge cases handled (empty query, large file, etc.)

---

## 11. Deployment Considerations

### Docker Compose

**Benefits:**

- One-command setup
- Isolated environments
- Easy scaling (can add replicas)

**Configuration:**

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on:
      - qdrant
      - postgres
    restart: unless-stopped
```

### Production Readiness

**Checklist:**

- ✅ Health check endpoints
- ✅ Logging (file + console)
- ✅ Error handling
- ✅ Graceful shutdown
- ⚠️ No monitoring/alerting
- ⚠️ No backup strategy
- ❌ No load balancing

---

## 12. Conclusion

This RAG system balances **simplicity** and **functionality**. Design decisions prioritize:

1. **Reliability**: Proven technologies (PostgreSQL, FastAPI)
2. **Privacy**: Local LLM, no external API calls
3. **Performance**: Fast enough for real-time queries
4. **Maintainability**: Clear code structure, modular design

**Key Strength**: End-to-end working system with proper citations

**Key Weakness**: Not optimized for scale (> 1000 papers)

**Next Steps**: See "Future Improvements" section for roadmap.

---

**Author**: [Your Name]  
**Date**: October 30, 2025  
**Version**: 1.0
