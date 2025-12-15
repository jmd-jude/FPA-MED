"""Pydantic models for API requests and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for document queries."""
    query: str
    case_id: Optional[str] = None


class Source(BaseModel):
    """Source citation model."""
    doc_id: str
    snippet: str
    relevance_score: float


class QueryResponse(BaseModel):
    """Response model for document queries."""
    answer: str
    sources: List[Source]
    metadata: Dict[str, Any]


class Case(BaseModel):
    """Case information model."""
    case_id: str
    title: str
    date: str
    document_count: int


class CasesResponse(BaseModel):
    """Response model for listing cases."""
    cases: List[Case]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    vector_db: str
    documents_loaded: int


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    case_id: str
    metadata: Optional[Dict[str, Any]] = None
    force_reingest: bool = False
    clear_first: bool = False


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    status: str
    documents_added: int
    documents_skipped: int = 0


class CaseSearchRequest(BaseModel):
    """Request model for case search."""
    description: str


class CaseSearchResult(BaseModel):
    """Result model for individual case search result."""
    case_id: str
    title: str
    relevance_score: float
    summary: str
    key_findings: List[str]
    document_count: int
