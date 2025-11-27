"""Tests for FastAPI endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data


class TestEncodeDocEndpoint:
    """Tests for /encode_doc endpoint."""

    def test_encode_valid_document(self, client: TestClient, sample_document: Path):
        """Test encoding a valid document."""
        response = client.post(
            "/encode_doc",
            json={"file_path": str(sample_document)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["chunk_count"] > 0
        assert len(data["token_counts"]) == data["chunk_count"]

    def test_encode_nonexistent_document(self, client: TestClient):
        """Test encoding nonexistent document returns 404.

        **Feature: semantic-knowledge-base, Property 10: Input Validation**
        **Validates: Requirements 8.2, 8.5**
        """
        response = client.post(
            "/encode_doc",
            json={"file_path": "/nonexistent/path/doc.md"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_encode_directory_returns_400(
        self, client: TestClient, sample_documents_dir: Path
    ):
        """Test encoding a directory returns 400.

        **Feature: semantic-knowledge-base, Property 10: Input Validation**
        **Validates: Requirements 8.1, 8.5**
        """
        response = client.post(
            "/encode_doc",
            json={"file_path": str(sample_documents_dir)},
        )

        assert response.status_code == 400

    def test_encode_missing_file_path(self, client: TestClient):
        """Test request without file_path returns 422."""
        response = client.post("/encode_doc", json={})

        assert response.status_code == 422


class TestEncodeBatchEndpoint:
    """Tests for /encode_batch endpoint."""

    def test_encode_batch_valid_directory(
        self, client: TestClient, sample_documents_dir: Path
    ):
        """Test batch encoding a valid directory."""
        response = client.post(
            "/encode_batch",
            json={
                "directory_path": str(sample_documents_dir),
                "file_patterns": ["*.txt", "*.md"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["documents_queued"] > 0

    def test_encode_batch_nonexistent_directory(self, client: TestClient):
        """Test batch encoding nonexistent directory returns 404.

        **Feature: semantic-knowledge-base, Property 10: Input Validation**
        **Validates: Requirements 8.2, 8.5**
        """
        response = client.post(
            "/encode_batch",
            json={"directory_path": "/nonexistent/directory"},
        )

        assert response.status_code == 404

    def test_encode_batch_file_instead_of_directory(
        self, client: TestClient, sample_document: Path
    ):
        """Test batch encoding a file returns 400."""
        response = client.post(
            "/encode_batch",
            json={"directory_path": str(sample_document)},
        )

        assert response.status_code == 400

    def test_encode_batch_empty_directory(self, client: TestClient, tmp_path: Path):
        """Test batch encoding empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        response = client.post(
            "/encode_batch",
            json={"directory_path": str(empty_dir)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["documents_queued"] == 0


class TestQueryEndpoint:
    """Tests for /query endpoint."""

    def test_query_valid(self, client: TestClient, sample_document: Path):
        """Test valid query after encoding a document."""
        # First encode a document
        client.post(
            "/encode_doc",
            json={"file_path": str(sample_document)},
        )

        # Then query
        response = client.post(
            "/query",
            json={"query": "What is a vector database?", "top_k": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "results" in data

    def test_query_empty_rejected(self, client: TestClient):
        """Test empty query is rejected.

        **Feature: semantic-knowledge-base, Property 10: Input Validation**
        **Validates: Requirements 8.5**
        """
        response = client.post(
            "/query",
            json={"query": ""},
        )

        assert response.status_code == 422

    def test_query_respects_top_k(self, client: TestClient, sample_document: Path):
        """Test query respects top_k parameter.

        **Feature: semantic-knowledge-base, Property 7: Search Results Ordering**
        **Validates: Requirements 3.6**
        """
        # Encode document first
        client.post(
            "/encode_doc",
            json={"file_path": str(sample_document)},
        )

        # Query with specific top_k
        response = client.post(
            "/query",
            json={"query": "vector database", "top_k": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2

    def test_query_results_ordered_by_relevance(
        self, client: TestClient, sample_document: Path
    ):
        """Test query results are ordered by relevance score.

        **Feature: semantic-knowledge-base, Property 7: Search Results Ordering**
        **Validates: Requirements 3.5, 3.6**
        """
        # Encode document first
        client.post(
            "/encode_doc",
            json={"file_path": str(sample_document)},
        )

        response = client.post(
            "/query",
            json={"query": "semantic search embeddings", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["results"]) > 1:
            scores = [r["relevance_score"] for r in data["results"]]
            # Scores should be in descending order
            assert scores == sorted(scores, reverse=True)

    def test_query_default_top_k(self, client: TestClient):
        """Test query uses default top_k of 5."""
        response = client.post(
            "/query",
            json={"query": "test query"},
        )

        assert response.status_code == 200
        # Default top_k is 5, so at most 5 results
        data = response.json()
        assert len(data["results"]) <= 5


class TestErrorResponses:
    """Tests for error response handling."""

    def test_invalid_json_body(self, client: TestClient):
        """Test invalid JSON body returns 422."""
        response = client.post(
            "/encode_doc",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_wrong_method(self, client: TestClient):
        """Test wrong HTTP method returns 405."""
        response = client.get("/encode_doc")
        assert response.status_code == 405

    def test_nonexistent_endpoint(self, client: TestClient):
        """Test nonexistent endpoint returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
