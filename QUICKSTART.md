# Quick Start - Phase 1 Implementation

## Context
This is a RAG prototype for forensic psychiatry expert witness work. The full architecture is in `ARCHITECTURE.md`.

## Current State
- ✅ Project structure created (all files exist as stubs)
- ✅ `.env` file populated with API keys
- ✅ Test documents in `backend/data/cases/case_001/` and `case_002/`
- ✅ Python venv created and dependencies installed

## Your Task: Implement Phase 1 - Backend MVP

### Files to Implement (in order):

1. **backend/config.py**
   - Load environment variables
   - Export config constants

2. **backend/models.py**
   - Pydantic models for QueryRequest, QueryResponse, Source, Case

3. **backend/rag_engine.py**
   - RAGEngine class
   - Use LlamaIndex with ChromaDB
   - Methods: initialize(), query(), get_cases()
   - See ARCHITECTURE.md for LlamaIndex setup pattern

4. **backend/ingest.py**
   - Script to load documents from `/backend/data/cases/`
   - Create embeddings and populate ChromaDB
   - Run once at startup

5. **backend/main.py**
   - FastAPI app with endpoints: /health, /query, /cases
   - CORS middleware for localhost:3000
   - Startup event to initialize RAG engine

### Key Constraints:
- Use **semantic search only** (no hybrid/keyword search needed for POC)
- ChromaDB persistent storage in `./data/chroma_db`
- Anthropic Claude API for LLM (model from .env)
- OpenAI embeddings (model from .env)
- Top-k retrieval = 5 chunks

### Test Success:
```bash
cd backend
source venv/bin/activate
python ingest.py  # Should process case_001 and case_002
uvicorn main:app --reload --port 8000
# Then test: curl http://localhost:8000/health
```

### Reference:
See `ARCHITECTURE.md` sections:
- "Backend Structure" 
- "RAG Pipeline Details"
- "Key Implementation Notes > For LlamaIndex Setup"

### Output Location:
Work directly in the existing stub files. Don't create new ones.