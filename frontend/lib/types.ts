/**
 * TypeScript types and interfaces for the RAG frontend
 */

export interface Source {
  doc_id: string;
  snippet: string;
  relevance_score: number;
}

export interface QueryRequest {
  query: string;
  case_id?: string;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  metadata: {
    total_chunks_retrieved: number;
    processing_time_ms: number;
  };
}

export interface Case {
  case_id: string;
  title: string;
  date: string;
  document_count: number;
}

export interface CasesResponse {
  cases: Case[];
}

export interface HealthResponse {
  status: string;
  vector_db: string;
  documents_loaded: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export interface CaseSearchRequest {
  description: string;
}

export interface CaseSearchResult {
  case_id: string;
  title: string;
  relevance_score: number;
  summary: string;
  key_findings: string[];
  document_count: number;
}
