"""Pydantic models for API requests/responses and LanceDB schema."""

from datetime import datetime
from typing import Any, Optional

from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel, Field


# =============================================================================
# LanceDB Schema Models
# =============================================================================


class ChunkSchema(LanceModel):
    """Schema for document chunks stored in LanceDB."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="Text content of the chunk")
    embedding: Vector(768) = Field(..., description="768-dimensional embedding vector")  # type: ignore[valid-type]
    source_document: str = Field(..., description="Source document identifier/path")
    chunk_offset: int = Field(
        ..., description="Character offset in the original document"
    )
    token_count: int = Field(..., description="Number of tokens in the chunk")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when chunk was created"
    )


# =============================================================================
# API Request Models
# =============================================================================


class EncodeDocRequest(BaseModel):
    """Request model for single document encoding."""

    file_path: str = Field(..., description="Absolute path to the document file")
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Optional metadata for the document"
    )


class EncodeBatchRequest(BaseModel):
    """Request model for batch document encoding from a directory."""

    directory_path: str = Field(..., description="Absolute path to the directory")
    file_patterns: Optional[list[str]] = Field(
        default=None,
        description="File patterns to include (e.g., ['*.txt', '*.md']). Defaults to common text formats.",
    )


class QueryRequest(BaseModel):
    """Request model for semantic search queries."""

    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(
        default=5, ge=1, le=100, description="Number of results to return"
    )


# =============================================================================
# API Response Models
# =============================================================================


class SearchResult(BaseModel):
    """Model for a single search result."""

    content: str = Field(..., description="Text content of the chunk")
    relevance_score: float = Field(..., description="Relevance score after reranking")
    source_document: str = Field(..., description="Source document identifier/path")
    chunk_offset: int = Field(..., description="Character offset in original document")


class EncodeDocResponse(BaseModel):
    """Response model for single document encoding."""

    status: str = Field(..., description="Operation status: 'success' or 'error'")
    message: str = Field(..., description="Status message")
    document_path: Optional[str] = Field(
        default=None, description="Path of the encoded document"
    )
    chunk_count: Optional[int] = Field(
        default=None, description="Number of chunks created"
    )
    token_counts: Optional[list[int]] = Field(
        default=None, description="Token count for each chunk"
    )


class EncodeBatchResponse(BaseModel):
    """Response model for batch document encoding."""

    status: str = Field(..., description="Operation status: 'success' or 'error'")
    message: str = Field(..., description="Status message")
    documents_queued: Optional[int] = Field(
        default=None, description="Number of documents queued for processing"
    )


class QueryResponse(BaseModel):
    """Response model for semantic search queries."""

    status: str = Field(..., description="Operation status: 'success' or 'error'")
    message: str = Field(..., description="Status message")
    results: list[SearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    query: Optional[str] = Field(default=None, description="The original query")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    status: str = Field(
        default="error", description="Always 'error' for error responses"
    )
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        default=None, description="Detailed error information"
    )
