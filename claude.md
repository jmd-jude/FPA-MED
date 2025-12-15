# Forensic Psychiatry RAG System - Claude Documentation

## Project Overview

A RAG (Retrieval-Augmented Generation) system for forensic psychiatry document analysis. Allows medical doctors to search through case documents, find similar cases, and get AI-powered answers with source citations.

**Tech Stack:**
- **Backend**: FastAPI + LlamaIndex + ChromaDB + Claude (Anthropic API)
- **Frontend**: Next.js 16 (React) + TypeScript + Tailwind CSS
- **Vector DB**: ChromaDB (persistent storage)
- **Embeddings**: OpenAI text-embedding-ada-002
- **LLM**: Claude Sonnet 4.5 (via Anthropic API)

## Architecture

```
┌─────────────────┐
│   Next.js App   │  (Frontend - Port 3000)
│   - Chat UI     │
│   - API Proxies │
└────────┬────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI Server │  (Backend - Port 8000)
│   - /query      │
│   - /cases      │
│   - /search-cases │
└────────┬────────┘
         │
         ├──► ChromaDB (Vector Store)
         ├──► OpenAI (Embeddings)
         └──► Anthropic Claude (LLM)
```

## Directory Structure

```
fpamed/
├── backend/
│   ├── main.py                 # FastAPI application & endpoints
│   ├── rag_engine.py          # Core RAG logic (LlamaIndex + ChromaDB)
│   ├── models.py              # Pydantic models for API
│   ├── config.py              # Configuration & environment variables
│   ├── ingest.py              # Document ingestion script
│   ├── data/
│   │   └── cases/
│   │       ├── case_001/
│   │       │   ├── metadata.json
│   │       │   └── *.pdf, *.txt
│   │       └── case_002/
│   └── chroma_db/             # Persistent vector database
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Main page (renders ChatInterface)
│   │   └── api/               # Next.js API routes (proxy to backend)
│   │       ├── health/route.ts
│   │       ├── cases/route.ts
│   │       ├── query/route.ts
│   │       └── search-cases/route.ts  # NEW: Case discovery
│   ├── components/
│   │   ├── ChatInterface.tsx   # Main chat component
│   │   ├── MessageList.tsx     # Message display
│   │   ├── QueryInput.tsx      # User input field
│   │   ├── CaseSelector.tsx    # Dropdown to filter by case
│   │   ├── CaseDiscovery.tsx   # NEW: Find similar cases modal
│   │   └── LoadingSpinner.tsx
│   └── lib/
│       ├── api.ts             # API client functions
│       └── types.ts           # TypeScript interfaces
│
├── CLEAR CONVO SPEC.MD        # Spec for clear conversation feature
├── CASE DISCOVERY SPEC.md     # Spec for case discovery feature
└── claude.md                  # This file
```

## Backend Components

### Main Endpoints (`main.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check, returns DB status |
| `/cases` | GET | List all available cases |
| `/query` | POST | Query documents with optional case filter |
| `/search-cases` | POST | Find similar cases by description (semantic search) |
| `/ingest` | POST | Ingest new documents into vector DB |

### RAG Engine (`rag_engine.py`)

**Key Methods:**
- `initialize()`: Sets up LlamaIndex, ChromaDB, embeddings, and LLM
- `query(query_text, case_id=None)`: Searches documents and generates answer
- `search_cases(description, top_k=5)`: Semantic search across cases
- `get_cases()`: Returns list of all cases with metadata
- `ingest_documents(case_dir, case_id)`: Adds documents to vector store

**Configuration:**
- Uses Claude Sonnet 4.5 for response generation
- OpenAI embeddings for vector search
- ChromaDB for persistent vector storage
- Supports metadata filtering by case_id

### Models (`models.py`)

```python
# Request/Response Models
QueryRequest(query: str, case_id: Optional[str])
QueryResponse(answer: str, sources: List[Source], metadata: dict)
CaseSearchRequest(description: str)
CaseSearchResult(case_id, title, relevance_score, summary, key_findings, document_count)
Case(case_id, title, date, document_count)
Source(doc_id, snippet, relevance_score)
```

## Frontend Components

### Main Components

**ChatInterface.tsx** - Orchestrates the entire UI:
- Manages messages, selected case, loading states
- Integrates CaseDiscovery, CaseSelector, MessageList, QueryInput
- Handles message submission and API calls

**CaseDiscovery.tsx** - NEW: Find similar cases:
- Modal with text input for case description
- Calls `/api/search-cases` endpoint
- Displays ranked results with relevance scores
- "Filter to This Case" button to apply case filter

**CaseSelector.tsx** - Dropdown filter:
- Shows "All Cases" or specific case
- Filters query results by case_id

**MessageList.tsx** - Message display:
- Shows user questions and assistant answers
- Displays source citations with relevance scores

**QueryInput.tsx** - User input:
- Text area with submit button
- Disabled during loading

### API Client (`lib/api.ts`)

```typescript
queryDocuments(request: QueryRequest): Promise<QueryResponse>
getCases(): Promise<CasesResponse>
searchCases(description: string): Promise<CaseSearchResult[]>
getHealth(): Promise<HealthResponse>
```

All API calls go through Next.js API routes which proxy to the FastAPI backend.

## Recent Features

### 1. Clear Conversation (Implemented)
**Location**: `ChatInterface.tsx:84-87, 96-101`

Adds a "Clear Conversation" button in the header that resets:
- All messages to empty array
- Selected case filter to null

### 2. Case Discovery (Implemented)
**Spec**: `CASE DISCOVERY SPEC.md`

**Backend Changes**:
- Added `CaseSearchRequest` and `CaseSearchResult` models
- New `/search-cases` endpoint in `main.py:109-125`
- Implemented `search_cases()` in `rag_engine.py:224-312`
  - Uses semantic search on existing vector embeddings
  - Deduplicates by case_id
  - Returns top 5 most relevant cases with scores

**Frontend Changes**:
- Created `CaseDiscovery.tsx` component with modal UI
- Added `searchCases()` API function
- Created `/app/api/search-cases/route.ts` proxy
- Integrated into `ChatInterface.tsx` above case selector

**How It Works**:
1. User clicks "Find Similar Cases" button
2. Enters description (e.g., "Competency evaluation for schizophrenia patient")
3. System performs semantic search across all case embeddings
4. Returns ranked cases with relevance scores, summaries, key findings
5. User can click "Filter to This Case" to select a case

## Data Structure

### Case Metadata (`metadata.json`)

```json
{
  "case_id": "case_001",
  "title": "State v. Anderson - Competency Evaluation",
  "date": "2024-01-15",
  "summary": "Brief case summary for semantic search",
  "key_findings": [
    "Defendant competent to stand trial",
    "Major depressive disorder in remission"
  ],
  "documents": ["report.pdf", "interview.txt"]
}
```

### ChromaDB Collections

**Main Collection**: `forensic_cases`
- Stores document chunks with embeddings
- Metadata includes: `case_id`, `file_name`, other custom fields
- Used for both document query and case search

## Development Workflow

### Starting the Servers

**Backend** (from `/backend`):
```bash
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Frontend** (from `/frontend`):
```bash
npm run dev
```

### Adding a New Case

1. Create directory: `backend/data/cases/case_XXX/`
2. Add `metadata.json` with case info
3. Add documents (PDF, TXT, DOCX)
4. Run ingestion (if auto-ingest not enabled)

### Adding a New API Endpoint

1. Add Pydantic models to `backend/models.py`
2. Import models in `backend/main.py`
3. Create endpoint function in `main.py`
4. Add TypeScript types to `frontend/lib/types.ts`
5. Add API function to `frontend/lib/api.ts`
6. Create Next.js API route in `frontend/app/api/[endpoint]/route.ts`

## Environment Variables

### Backend (`.env`)
```
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
EMBEDDING_MODEL=text-embedding-ada-002
```

### Frontend
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Common Issues & Solutions

### Issue: "Unknown error" in Case Discovery
**Cause**: Missing Next.js API route proxy
**Solution**: Create `/frontend/app/api/search-cases/route.ts`

### Issue: Backend won't start - "Unknown model"
**Cause**: LlamaIndex doesn't recognize new Claude models
**Solution**: Model name patching is in `rag_engine.py:16-31`

### Issue: No search results
**Cause**: ChromaDB might be empty or case_id metadata missing
**Solution**: Re-run ingestion with proper metadata

### Issue: CORS errors
**Cause**: Frontend trying to call backend directly instead of through proxy
**Solution**: Always use `/api/*` routes, not direct backend URLs

## Key Files to Know

| File | Purpose | When to Edit |
|------|---------|--------------|
| `backend/models.py` | API contracts | Adding new endpoints |
| `backend/main.py` | API endpoints | Adding new routes |
| `backend/rag_engine.py` | Core RAG logic | Changing search/retrieval |
| `frontend/components/ChatInterface.tsx` | Main UI orchestration | Adding UI features |
| `frontend/lib/api.ts` | API client | Adding API calls |
| `frontend/lib/types.ts` | TypeScript types | Matching backend models |

## Performance Notes

- First query is slower (LLM initialization)
- Embeddings are cached in ChromaDB
- Case search is faster than document query (fewer vectors)
- LlamaIndex uses similarity_top_k=5 for retrieval

## Security Considerations

- API keys in environment variables (not committed)
- Next.js API routes act as backend proxy (no direct exposure)
- No authentication implemented yet (future enhancement)
- CORS configured for localhost development

## Future Enhancements (from specs)

- Multi-case filtering (select multiple cases at once)
- Case similarity explanations (why cases match)
- Saved searches and case collections
- Export case comparisons side-by-side
- Enhanced metadata with diagnoses, legal questions, outcomes
- Separate ChromaDB collection for case summaries (Option B from spec)

## Testing

**Backend endpoint test**:
```bash
curl -X POST http://localhost:8000/search-cases \
  -H "Content-Type: application/json" \
  -d '{"description": "competency evaluation schizophrenia"}'
```

**Frontend**: Navigate to http://localhost:3000

## Git Workflow

- Main branch: `main` (or `master`)
- Feature specs in root: `*.MD`, `*.md`
- No `.git` in subdirectories
- Environment files in `.gitignore`

---

**Last Updated**: 2025-12-15
**Major Features**: Document Query, Case Filtering, Case Discovery, Clear Conversation
