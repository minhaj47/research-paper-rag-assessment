# Paper Filtering Feature Documentation

## Overview

This feature allows users to filter query results by specific papers, enabling more targeted searches across selected research papers.

## API Changes

### Backend

#### 1. **POST /api/query** - Enhanced endpoint

**Previous**:

```python
POST /api/query?query=<question>&top_k=5
```

**Now**:

```python
POST /api/query?query=<question>&top_k=5&paper_ids=1&paper_ids=3
```

**Parameters**:

- `query` (string, required): The research question
- `top_k` (int, optional, default=5): Number of relevant chunks to retrieve
- `paper_ids` (List[int], optional): List of paper IDs to filter by

**Example Request**:

```bash
curl -X POST "http://localhost:8000/api/query?query=What methodology was used in the transformer paper?&top_k=5&paper_ids=1&paper_ids=3"
```

**Response** (unchanged):

```json
{
  "query": "What methodology was used in the transformer paper?",
  "answer": "The transformer architecture uses self-attention...",
  "citations": [
    {
      "paper_title": "Attention is All You Need",
      "section": "Methodology",
      "page_number": 3,
      "text": "...",
      "relevance_score": 0.89
    }
  ],
  "response_time": 1.23
}
```

## Implementation Details

### Backend Changes

#### 1. **Qdrant Client** (`src/services/qdrant_client.py`)

**Added Filter Support**:

```python
from qdrant_client.models import Filter, FieldCondition, MatchAny

def search_similar(self, query_embedding, limit=5, score_threshold=0.3, paper_ids=None):
    """Search with optional paper_ids filter"""
    query_filter = None

    if paper_ids and len(paper_ids) > 0:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="paper_id",
                    match=MatchAny(any=paper_ids)
                )
            ]
        )

    results = self.client.search(
        collection_name=self.collection_name,
        query_vector=query_embedding,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=query_filter  # Apply filter
    )
    return results
```

**Key Changes**:

- Added `paper_ids` parameter to `search_similar()`
- Implemented Qdrant `Filter` with `MatchAny` condition
- Paper ID is now stored in chunk payload for filtering

#### 2. **RAG Pipeline** (`src/services/rag_pipeline.py`)

**Updated Methods**:

1. `process_and_store_document()` - Now accepts and stores `paper_id`
2. `query()` - Now accepts `paper_ids` parameter and passes to vector search

```python
async def query(self, query: str, top_k: int = 5, paper_ids: List[int] = None):
    """Query with optional paper filtering"""
    query_embedding = await asyncio.to_thread(
        self.embedding_service.get_embeddings, query
    )

    results = await asyncio.to_thread(
        self.vector_store.search_similar,
        query_embedding.tolist(),
        top_k,
        0.3,
        paper_ids  # Pass filter
    )
    # ... rest of the logic
```

#### 3. **API Routes** (`src/api/routes.py`)

**Query Endpoint**:

```python
@router.post("/query")
async def query_papers(
    query: str,
    top_k: int = 5,
    paper_ids: List[int] = None,  # NEW
    db: Session = Depends(get_db)
):
    """Query with optional paper filtering"""
    result = await rag_pipeline.query(query, top_k, paper_ids)
    # ... rest
```

**Upload Endpoint**:

- Now stores paper twice: first without ID, then updates with ID after DB insertion
- This ensures the paper_id is available for filtering

### Frontend Changes

#### 1. **API Client** (`frontend/lib/api.ts`)

**Updated query method**:

```typescript
query: async (
  query: string,
  topK = 5,
  paperIds?: number[]
): Promise<QueryResult> => {
  const params: any = { query, top_k: topK };
  if (paperIds && paperIds.length > 0) {
    params.paper_ids = paperIds;
  }
  const response = await api.post("/api/query", null, { params });
  return response.data;
};
```

#### 2. **Query Interface** (`frontend/components/QueryInterface.tsx`)

**New State Variables**:

```typescript
const [papers, setPapers] = useState<Paper[]>([]);
const [selectedPaperIds, setSelectedPaperIds] = useState<number[]>([]);
const [loadingPapers, setLoadingPapers] = useState(false);
```

**New Functions**:

- `loadPapers()` - Fetches available papers on mount
- `handlePaperToggle()` - Toggles paper selection
- `handleSelectAll()` - Selects/deselects all papers

**UI Components Added**:

1. **Paper Selection Card**: Shows list of papers with checkboxes
2. **Select All/Deselect All**: Quick toggle button
3. **Selection Counter**: Shows how many papers are selected
4. **Paper Details**: Each paper shows title, author, pages, and chunks

## User Experience

### UI Flow

1. **User enters query** in the text area
2. **User sees paper filter section** (if papers exist)
3. **User can**:
   - Select specific papers to search
   - Select all papers (searches all)
   - Deselect all (searches all)
4. **Visual feedback**:
   - Selected count displayed
   - Checkboxes show selection state
   - Info text explains current selection
5. **Submit query** - Only searches in selected papers

### Behavior

| Selection State                    | Behavior                          |
| ---------------------------------- | --------------------------------- |
| No papers selected (all unchecked) | Searches **all papers**           |
| All papers selected                | Searches **all papers**           |
| Some papers selected               | Searches **only selected papers** |

**Why?** If nothing is selected, we assume user wants all papers. This provides better UX than blocking the search.

## Visual Design

### Paper Filter Section

```
┌─────────────────────────────────────────────────┐
│ Filter by Papers (2 selected)    [Deselect All] │
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑ Attention is All You Need                 │ │
│ │   by Vaswani et al.                         │ │
│ │   12 pages • 45 chunks                      │ │
│ │                                             │ │
│ │ ☐ BERT: Pre-training of Deep...            │ │
│ │   by Devlin et al.                          │ │
│ │   16 pages • 58 chunks                      │ │
│ │                                             │ │
│ │ ☑ GPT-3: Language Models are...            │ │
│ │   by Brown et al.                           │ │
│ │   75 pages • 234 chunks                     │ │
│ └─────────────────────────────────────────────┘ │
│ Searching in 2 selected papers                  │
└─────────────────────────────────────────────────┘
```

### Styling

- **Background**: White card with border
- **Max Height**: 240px with scroll
- **Hover Effect**: Light gray background on paper items
- **Checkbox**: Blue accent color
- **Typography**:
  - Title: 14px, medium weight
  - Author: 12px, muted color
  - Metadata: 12px, lighter color

## Testing

### Test Cases

1. **No Papers Selected**

   - Expected: Query searches all papers
   - Backend receives: `paper_ids=None`

2. **All Papers Selected**

   - Expected: Query searches all papers
   - Backend receives: `paper_ids=None` (optimization)

3. **Specific Papers Selected**

   - Expected: Query searches only selected papers
   - Backend receives: `paper_ids=[1, 3]`

4. **No Papers Uploaded**
   - Expected: Paper filter section not shown
   - Query works as before (returns no results with helpful error)

### Example Test Query

```bash
# Query specific papers
curl -X POST "http://localhost:8000/api/query" \
  -G \
  --data-urlencode "query=What methodology was used?" \
  --data-urlencode "top_k=5" \
  --data-urlencode "paper_ids=1" \
  --data-urlencode "paper_ids=3"
```

## Benefits

1. **Targeted Search**: Find information in specific papers
2. **Comparison**: Compare specific papers by limiting search scope
3. **Performance**: Potentially faster searches with fewer papers
4. **Relevance**: More relevant results from known papers
5. **Flexibility**: Optional feature - works with or without filtering

## Limitations

1. **Paper must exist**: Paper IDs must be valid in the database
2. **No validation**: Backend doesn't validate paper IDs exist (yet)
3. **Re-indexing**: Existing papers need to be re-uploaded to have paper_id in vector store

## Future Enhancements

- [ ] Add paper ID validation in backend
- [ ] Show paper count in results
- [ ] Add "Recent papers" quick filter
- [ ] Add "Favorite papers" feature
- [ ] Save filter preferences
- [ ] Bulk re-index existing papers with IDs
- [ ] Add paper tags for topic-based filtering
- [ ] Show which papers contributed to answer

## Migration Notes

### For Existing Installations

If you have existing papers in the system:

1. **Option A: Re-upload papers**

   - Delete existing papers
   - Re-upload them to get paper_ids in vector store

2. **Option B: Migration script** (Coming soon)
   - Script to update existing vectors with paper_ids

### Database Schema

No schema changes needed - paper_id already exists in papers table.

### Vector Store

Existing vectors won't have `paper_id` in payload. They will be skipped when filtering is used.

## Summary

This feature adds powerful filtering capabilities to the RAG system, allowing users to:

- ✅ Target specific papers in their queries
- ✅ Get more relevant results from known papers
- ✅ Compare specific papers side-by-side
- ✅ Maintain backwards compatibility (filtering is optional)

The implementation is clean, efficient, and user-friendly with a modern UI that fits the academic theme.
