"""FastAPI application for the RAG backend."""

from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from rag_engine import RAGEngine
from models import (
    QueryRequest,
    QueryResponse,
    CasesResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    CaseSearchRequest,
    CaseSearchResult,
)
from config import ALLOWED_ORIGINS


# Global RAG engine instance
rag_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    global rag_engine
    print("Initializing RAG engine...")
    rag_engine = RAGEngine()
    rag_engine.initialize()
    print("RAG engine initialized successfully")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Forensic Psychiatry RAG API",
    description="RAG system for forensic psychiatry document analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    doc_count = rag_engine.get_document_count()

    return HealthResponse(
        status="ok",
        vector_db="connected",
        documents_loaded=doc_count,
    )


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = rag_engine.query(
            query_text=request.query,
            case_id=request.case_id,
        )

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            metadata=result["metadata"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/cases", response_model=CasesResponse)
async def list_cases():
    """List all available cases."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    try:
        cases = rag_engine.get_cases()
        return CasesResponse(cases=cases)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cases: {str(e)}")


@app.post("/search-cases", response_model=List[CaseSearchResult])
async def search_cases(request: CaseSearchRequest):
    """
    Find cases similar to user's description.
    Uses semantic search on case metadata/summaries.
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    if not request.description or not request.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    try:
        results = rag_engine.search_cases(request.description, top_k=5)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Case search failed: {str(e)}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest):
    """Ingest new documents into the system (for demo purposes)."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")

    try:
        from pathlib import Path
        from config import DATA_DIR

        # Handle clear_first flag
        if request.clear_first:
            success = rag_engine.clear_all_documents()
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to clear vector store"
                )

        case_dir = Path(DATA_DIR) / request.case_id
        if not case_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Case directory not found: {request.case_id}"
            )

        result = rag_engine.ingest_documents(
            case_dir=str(case_dir),
            case_id=request.case_id,
            metadata=request.metadata,
            force_reingest=request.force_reingest,
        )

        return IngestResponse(
            status="success",
            documents_added=result.get('ingested', 0),
            documents_skipped=result.get('skipped', 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    from config import BACKEND_HOST, BACKEND_PORT

    uvicorn.run(
        "main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=True,
    )
