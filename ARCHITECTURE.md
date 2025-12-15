# Forensic Psychiatry RAG Prototype - Architecture Specification

## Project Overview

**Purpose**: Rapid prototype demonstrating AI-powered document retrieval and analysis for forensic psychiatry expert witness work.

**Scope**: Functional demo with synthetic data to validate interaction patterns, gather stakeholder feedback, and inform vendor selection/PRD development.

**Non-Goals**: Production deployment, real data handling, HIPAA compliance implementation (prototype only).

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐         │
│  │ Chat UI    │  │ Document   │  │ Case         │         │
│  │ Interface  │  │ Viewer     │  │ Selector     │         │
│  └────────────┘  └────────────┘  └──────────────┘         │
│         │                │                 │               │
│         └────────────────┴─────────────────┘               │
│                          │                                  │
│                   API Routes (Next.js)                      │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTP/JSON
┌──────────────────────────┼──────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌─────────────────────────────────────────────────┐       │
│  │              RAG Engine (LlamaIndex)            │       │
│  │  ┌──────────────┐  ┌─────────────┐            │       │
│  │  │ Document     │  │ Query       │            │       │
│  │  │ Ingestion    │  │ Processing  │            │       │
│  │  └──────────────┘  └─────────────┘            │       │
│  └─────────────────────────────────────────────────┘       │
│                          │                                  │
│  ┌─────────────────────────────────────────────────┐       │
│  │         Vector Store (ChromaDB - Local)         │       │
│  └─────────────────────────────────────────────────┘       │
│                          │                                  │
│  ┌─────────────────────────────────────────────────┐       │
│  │         LLM Provider (Claude via Anthropic)     │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Document Ingestion**:
1. Synthetic case documents stored in `/backend/data/cases/`
2. Backend startup script loads documents into ChromaDB
3. Documents chunked (512 tokens, 50 token overlap)
4. Embeddings generated (OpenAI text-embedding-3-small)
5. Stored in local ChromaDB with metadata (case_id, doc_type, date)

**Query Processing**:
1. User submits query via frontend chat interface
2. Next.js API route forwards to FastAPI `/query` endpoint
3. LlamaIndex retrieves relevant chunks (top-k=5)
4. Context + query sent to Claude API
5. Response streamed back through API layers to frontend

---

## API Contract

### Backend API (FastAPI)

**Base URL**: `http://localhost:8000`

#### Endpoints

**1. Health Check**
```
GET /health
Response: { "status": "ok", "vector_db": "connected", "documents_loaded": 42 }
```

**2. Query Documents**
```
POST /query
Content-Type: application/json

Request:
{
  "query": "What were the key findings in the Smith case evaluation?",
  "case_id": "case_001" // optional, filters to specific case
}

Response:
{
  "answer": "Based on the evaluation...",
  "sources": [
    {
      "doc_id": "case_001_eval_report",
      "snippet": "The defendant exhibited...",
      "relevance_score": 0.89
    }
  ],
  "metadata": {
    "total_chunks_retrieved": 5,
    "processing_time_ms": 1240
  }
}
```

**3. List Cases**
```
GET /cases
Response:
{
  "cases": [
    {
      "case_id": "case_001",
      "title": "State v. Smith - Competency Evaluation",
      "date": "2024-03-15",
      "document_count": 8
    }
  ]
}
```

**4. Ingest Documents** (for demo purposes)
```
POST /ingest
Content-Type: multipart/form-data

Request:
{
  "files": [File, File],
  "case_id": "case_002",
  "metadata": { ... }
}

Response:
{
  "status": "success",
  "documents_added": 2
}
```

### Frontend API Routes (Next.js)

**Base URL**: `http://localhost:3000`

These routes proxy to the backend:

```
POST /api/query        → Backend /query
GET  /api/cases        → Backend /cases
GET  /api/health       → Backend /health
```

---

## Frontend Structure

### Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks (useState, useReducer)
- **HTTP Client**: fetch API

### File Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page with chat interface
│   ├── api/
│   │   ├── query/route.ts      # Proxy to backend /query
│   │   ├── cases/route.ts      # Proxy to backend /cases
│   │   └── health/route.ts     # Proxy to backend /health
│   └── globals.css             # Tailwind imports
├── components/
│   ├── ChatInterface.tsx       # Main chat UI
│   ├── MessageList.tsx         # Display messages
│   ├── QueryInput.tsx          # Input field + submit
│   ├── CaseSelector.tsx        # Dropdown for case filtering
│   ├── SourceCard.tsx          # Display source citations
│   └── LoadingSpinner.tsx      # Loading states
├── lib/
│   ├── api.ts                  # API client functions
│   └── types.ts                # TypeScript interfaces
├── public/
│   └── sample-docs/            # Sample PDFs for UI demo
└── package.json
```

### Key Components

#### ChatInterface.tsx
```typescript
// State: messages[], currentQuery, selectedCase, isLoading
// Features: 
// - Send query to backend
// - Display message history
// - Show source citations
// - Case filter dropdown
```

#### MessageList.tsx
```typescript
// Props: messages[]
// Features:
// - Render user/assistant messages
// - Display source cards for assistant responses
// - Auto-scroll to bottom
```

#### SourceCard.tsx
```typescript
// Props: source { doc_id, snippet, relevance_score }
// Features:
// - Show document name
// - Display relevant snippet
// - Relevance score indicator
```

---

## Backend Structure

### Technology Stack
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **RAG Orchestration**: LlamaIndex
- **Vector Store**: ChromaDB (local, persistent)
- **LLM**: Anthropic Claude (via API)
- **Embeddings**: OpenAI text-embedding-3-small

### File Structure

```
backend/
├── main.py                     # FastAPI app entry point
├── rag_engine.py               # LlamaIndex RAG logic
├── models.py                   # Pydantic models (request/response)
├── config.py                   # Configuration management
├── ingest.py                   # Document ingestion script
├── data/
│   ├── cases/                  # Synthetic case documents
│   │   ├── case_001/
│   │   │   ├── evaluation_report.pdf
│   │   │   ├── court_testimony.txt
│   │   │   └── metadata.json
│   │   └── case_002/
│   └── chroma_db/              # ChromaDB storage (gitignored)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # Backend setup instructions
```

### Key Modules

#### main.py
```python
# FastAPI application
# Endpoints: /query, /cases, /health, /ingest
# CORS middleware for frontend connection
# Startup event: Initialize RAG engine
```

#### rag_engine.py
```python
# RAGEngine class
# Methods:
# - initialize(): Load documents, create index
# - query(query_text, case_id): Retrieve + generate
# - get_cases(): List available cases
# - ingest_documents(): Add new documents
```

#### models.py
```python
# Pydantic models:
# - QueryRequest
# - QueryResponse
# - Source
# - Case
# - IngestRequest
```

#### ingest.py
```python
# Script to process synthetic documents
# Creates embeddings and populates ChromaDB
# Run once at startup or when adding cases
```

---

## RAG Pipeline Details

### Document Processing

**Supported Formats**: PDF, TXT, DOCX (via LlamaIndex readers)

**Chunking Strategy**:
- Chunk size: 512 tokens
- Overlap: 50 tokens
- Separator: Sentence boundaries (LlamaIndex default)

**Metadata Schema**:
```python
{
  "case_id": "case_001",
  "doc_type": "evaluation_report",  # evaluation_report, testimony, correspondence, etc.
  "date": "2024-03-15",
  "source_file": "evaluation_report.pdf",
  "page": 3  # if applicable
}
```

### Query Processing

**Retrieval Strategy**:
- Similarity search: Cosine similarity on embeddings
- Top-k: 5 chunks by default
- Optional filtering: by case_id, doc_type, date range

**Prompt Template**:
```
You are an AI assistant helping forensic psychiatry experts analyze case documents.

Context from relevant documents:
{retrieved_context}

User question: {query}

Provide a comprehensive answer based on the context. If the context doesn't contain 
enough information, say so. Always cite which documents you're referencing.
```

**Response Generation**:
- Model: Claude Sonnet 4-5
- Max tokens: 1000
- Temperature: 0.3 (for consistency)
- Stream: Yes (for better UX)

---

## Environment Configuration

### Backend .env Template

```bash
# .env fill in values

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03--VZ6AxJSssZ4VYV...

# OpenAI API (for embeddings)
OPENAI_API_KEY=sk-proj-vpC8nLtZ3ZLE5vXoi...

# Vector DB
CHROMA_PERSIST_DIR=./data/chroma_db

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CORS (for development)
ALLOWED_ORIGINS=http://localhost:3000

# LLM Settings
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1000

# Embedding Settings
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
```

### Frontend .env.local Template

```bash
# .env.local

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics, etc.
```

---

## Synthetic Data Requirements

### Case Document Types

Each case should include:

1. **Evaluation Report** (PDF/DOCX)
   - Psychiatric assessment
   - Mental status exam findings
   - Diagnosis
   - Opinions on competency/sanity/risk

2. **Court Testimony Transcript** (TXT)
   - Direct examination
   - Cross-examination
   - Redirect

3. **Case Correspondence** (TXT/PDF)
   - Letters to attorneys
   - Clarification requests
   - Follow-up notes

4. **Medical Records Summary** (PDF)
   - Relevant history
   - Previous hospitalizations
   - Medication records

### Metadata File (metadata.json)

```json
{
  "case_id": "case_001",
  "title": "State v. Smith - Competency Evaluation",
  "defendant": "John Smith (fictional)",
  "date": "2024-03-15",
  "court": "Superior Court of [State]",
  "evaluator": "Dr. Jane Doe, MD (fictional)",
  "question": "Competency to stand trial",
  "documents": [
    {
      "filename": "evaluation_report.pdf",
      "type": "evaluation_report",
      "date": "2024-03-15"
    },
    {
      "filename": "court_testimony.txt",
      "type": "testimony",
      "date": "2024-04-20"
    }
  ]
}
```

---

## Development Workflow

### Initial Setup

1. **Clone/Create Project Structure**
   ```bash
   cd ~/dev/fpamed
   # frontend/ already created
   # backend/ already created
   ```

2. **Backend Setup**
   ```bash
   cd backend
   source venv/bin/activate
   cp .env.example .env
   # Edit .env with API keys // already created
   ```

3. **Create Synthetic Data**
   - Generate 3-5 complete case folders
   - Place in `backend/data/cases/`
   - Each case has consistent metadata

4. **Ingest Documents**
   ```bash
   python ingest.py
   # Creates embeddings, populates ChromaDB
   ```

5. **Start Backend**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

6. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   cp .env.example .env.local
   # Edit .env.local if needed
   ```

7. **Start Frontend**
   ```bash
   npm run dev
   # Runs on http://localhost:3000
   ```

### Testing Workflow

**Unit Testing** (not required for prototype, but good to know):
- Backend: pytest
- Frontend: Jest + React Testing Library

**Manual Testing Checklist**:
- [ ] Load homepage, see chat interface
- [ ] Send query without case filter → get relevant results
- [ ] Filter by specific case → get case-specific results
- [ ] Verify source citations appear
- [ ] Test edge cases: empty query, no results, long query
- [ ] Check loading states work
- [ ] Verify error handling (backend down, API key invalid)

---

## Docker Compose (Optional but Recommended)

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend/data:/app/data
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    command: npm run dev

# One-command startup: docker-compose up
```

---

## Key Implementation Notes

### For LlamaIndex Setup

```python
# Basic pattern in rag_engine.py

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb

# Initialize components
Settings.llm = Anthropic(model="claude-sonnet-4-20250514", api_key=os.getenv("ANTHROPIC_API_KEY"))
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Create/load vector store
chroma_client = chromadb.PersistentClient(path="./data/chroma_db")
chroma_collection = chroma_client.get_or_create_collection("forensic_cases")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

# Load documents
documents = SimpleDirectoryReader("./data/cases", recursive=True).load_data()

# Create index
index = VectorStoreIndex.from_documents(documents, vector_store=vector_store)

# Query
query_engine = index.as_query_engine(similarity_top_k=5)
response = query_engine.query("What were the findings?")
```

### For Next.js API Routes

```typescript
// app/api/query/route.ts

export async function POST(request: Request) {
  const body = await request.json();
  
  const response = await fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  
  const data = await response.json();
  return Response.json(data);
}
```

---

## Success Criteria

### Functional Requirements
- [ ] User can ask questions about case documents
- [ ] System retrieves relevant context
- [ ] Claude generates coherent answers with citations
- [ ] Case filtering works correctly
- [ ] UI is responsive and intuitive

### Demo Requirements
- [ ] Can run with `docker-compose up` (or two terminal commands)
- [ ] Works with 3-5 synthetic cases
- [ ] Handles typical queries in < 5 seconds
- [ ] UI looks professional (not "data science notebook")
- [ ] Can export conversation history (nice-to-have)

### Deliverable Requirements
- [ ] Clear README with setup instructions
- [ ] Architecture doc (this file) explains all components
- [ ] Can demonstrate to COO and stakeholders
- [ ] Generates insights for vendor RFP/PRD
- [ ] Identifies technical constraints/considerations

---

## Next Steps for Implementation

### Phase 1: Backend MVP
1. Set up FastAPI skeleton
2. Implement basic RAG engine with LlamaIndex
3. Create 2-3 synthetic case folders
4. Test document ingestion
5. Verify query endpoint works

### Phase 2: Frontend MVP
1. Create chat interface component
2. Wire up API calls to backend
3. Display responses with loading states
4. Add basic styling with Tailwind

### Phase 3: Polish
1. Add case selector dropdown
2. Implement source citations display
3. Error handling and edge cases
4. UI/UX improvements
5. Docker Compose setup

### Phase 4: Demo Prep
1. Create 5 complete synthetic cases
2. Test end-to-end workflows
3. Prepare demo script
4. Document limitations and future work
5. Create vendor comparison matrix

---

## Technical Considerations for Production

*Note: These are NOT implemented in the prototype but should be documented for stakeholder discussions*

### Security & Compliance
- **HIPAA BAA**: AWS Bedrock or Azure OpenAI (with BAA)
- **Data Encryption**: At rest (AES-256) and in transit (TLS 1.3)
- **Access Control**: RBAC, audit logging
- **PHI Handling**: De-identification, secure deletion

### Scalability
- **Vector DB**: Migrate from ChromaDB to Pinecone/Qdrant
- **Document Storage**: S3-compatible with lifecycle policies
- **Caching**: Redis for frequent queries
- **Rate Limiting**: Per-user API quotas

### Accuracy & Quality
- **Evaluation Framework**: Precision/recall on known Q&A pairs
- **Human-in-the-Loop**: Review flagging for uncertain answers
- **Source Attribution**: Always cite specific documents/pages
- **Confidence Scores**: Surface when LLM is uncertain

### Cost Optimization
- **Embedding Cache**: Reuse embeddings for unchanged documents
- **LLM Selection**: Smaller models for simple queries
- **Batch Processing**: Async document ingestion
- **Usage Monitoring**: Track API costs per user/case

---

## Questions for COO/Stakeholders

Use the prototype to answer:

1. **User Workflows**: What are the top 5 query types doctors need?
2. **Document Types**: Are there critical document types we're missing?
3. **Integration**: Does this need to integrate with existing systems?
4. **Access Patterns**: Multi-user? Collaboration features?
5. **Accuracy Standards**: What error rate is acceptable?
6. **Response Time**: Is 3-5 seconds acceptable or need <1s?
7. **Build vs. Buy**: Should we build custom or use existing legal tech platforms?

---

## Appendix: Vendor Evaluation Criteria

*Use prototype learnings to evaluate potential partners*

### Technical Capabilities
- [ ] RAG accuracy on domain-specific documents
- [ ] HIPAA compliance infrastructure
- [ ] Scalability to 10,000+ documents
- [ ] Multi-modal support (PDFs, images, handwriting)
- [ ] API flexibility and customization

### Business Considerations
- [ ] Pricing model (per-user, per-query, flat fee)
- [ ] Implementation timeline
- [ ] Training and support offerings
- [ ] Data ownership and portability
- [ ] References from similar orgs (healthcare, legal)

### Risk Assessment
- [ ] Vendor financial stability
- [ ] Technology lock-in risk
- [ ] Data breach response plan
- [ ] Service level agreements (SLAs)
- [ ] Exit strategy and data migration

---

**End of Architecture Specification**

This document should be shared with Claude Code for implementation. Update as needed based on prototype learnings.