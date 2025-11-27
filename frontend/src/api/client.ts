/**
 * API client for the Knowledge Base backend
 */

import type { QueryRequest, QueryResponse, HealthResponse } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Perform a semantic search query
 */
export async function queryKnowledgeBase(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error: ${response.status}`);
  }

  return response.json();
}

/**
 * Check backend health
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}
