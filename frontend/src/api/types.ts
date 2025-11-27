/**
 * API types for the Knowledge Base backend
 */

export interface SearchResult {
  content: string;
  relevance_score: number;
  source_document: string;
  chunk_offset: number;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
}

export interface QueryResponse {
  status: string;
  message: string;
  results: SearchResult[];
  query: string;
}

export interface HealthResponse {
  status: string;
  app: string;
}
