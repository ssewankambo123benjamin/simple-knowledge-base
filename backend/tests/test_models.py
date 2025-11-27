"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models import (
    EncodeBatchRequest,
    EncodeBatchResponse,
    EncodeDocRequest,
    EncodeDocResponse,
    QueryRequest,
    QueryResponse,
    SearchResult,
)


class TestEncodeDocRequest:
    """Tests for EncodeDocRequest model."""

    def test_valid_request(self):
        """Test valid encode document request."""
        request = EncodeDocRequest(file_path="/path/to/doc.md")
        assert request.file_path == "/path/to/doc.md"
        assert request.metadata is None

    def test_with_metadata(self):
        """Test request with optional metadata."""
        request = EncodeDocRequest(
            file_path="/path/to/doc.md",
            metadata={"author": "test", "version": 1},
        )
        assert request.metadata == {"author": "test", "version": 1}

    def test_missing_file_path(self):
        """Test that file_path is required."""
        with pytest.raises(ValidationError):
            EncodeDocRequest()


class TestEncodeBatchRequest:
    """Tests for EncodeBatchRequest model."""

    def test_valid_request(self):
        """Test valid batch encode request."""
        request = EncodeBatchRequest(directory_path="/path/to/docs")
        assert request.directory_path == "/path/to/docs"
        assert request.file_patterns is None

    def test_with_patterns(self):
        """Test request with file patterns."""
        request = EncodeBatchRequest(
            directory_path="/path/to/docs",
            file_patterns=["*.md", "*.txt"],
        )
        assert request.file_patterns == ["*.md", "*.txt"]


class TestQueryRequest:
    """Tests for QueryRequest model."""

    def test_valid_request(self):
        """Test valid query request."""
        request = QueryRequest(query="test query")
        assert request.query == "test query"
        assert request.top_k == 5  # default

    def test_custom_top_k(self):
        """Test request with custom top_k."""
        request = QueryRequest(query="test", top_k=10)
        assert request.top_k == 10

    def test_empty_query_rejected(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValidationError):
            QueryRequest(query="")

    def test_top_k_bounds(self):
        """Test top_k validation bounds."""
        # Valid bounds
        QueryRequest(query="test", top_k=1)
        QueryRequest(query="test", top_k=100)

        # Invalid bounds
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=0)

        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=101)


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_valid_result(self):
        """Test valid search result."""
        result = SearchResult(
            content="test content",
            relevance_score=0.95,
            source_document="/path/doc.md",
            chunk_offset=100,
        )
        assert result.content == "test content"
        assert result.relevance_score == 0.95
        assert result.source_document == "/path/doc.md"
        assert result.chunk_offset == 100


class TestEncodeDocResponse:
    """Tests for EncodeDocResponse model."""

    def test_success_response(self):
        """Test successful encode response."""
        response = EncodeDocResponse(
            status="success",
            message="Encoded successfully",
            document_path="/path/doc.md",
            chunk_count=5,
            token_counts=[100, 200, 150, 180, 120],
        )
        assert response.status == "success"
        assert response.chunk_count == 5
        assert len(response.token_counts) == 5

    def test_error_response(self):
        """Test error encode response."""
        response = EncodeDocResponse(
            status="error",
            message="File not found",
        )
        assert response.status == "error"
        assert response.document_path is None


class TestQueryResponse:
    """Tests for QueryResponse model."""

    def test_with_results(self):
        """Test query response with results."""
        results = [
            SearchResult(
                content="result 1",
                relevance_score=0.9,
                source_document="/doc1.md",
                chunk_offset=0,
            ),
            SearchResult(
                content="result 2",
                relevance_score=0.8,
                source_document="/doc2.md",
                chunk_offset=100,
            ),
        ]
        response = QueryResponse(
            status="success",
            message="Found 2 results",
            results=results,
            query="test query",
        )
        assert len(response.results) == 2
        assert response.results[0].relevance_score > response.results[1].relevance_score

    def test_empty_results(self):
        """Test query response with no results."""
        response = QueryResponse(
            status="success",
            message="No results found",
            results=[],
            query="obscure query",
        )
        assert len(response.results) == 0
