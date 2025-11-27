"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.database import LanceDBManager
from app.main import app


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with temporary database path."""
    return Settings(
        lancedb_path=tempfile.mkdtemp(),
        table_name="test_chunks",
        debug=True,
    )


@pytest.fixture
def temp_db(test_settings: Settings) -> Generator[LanceDBManager, None, None]:
    """Create a temporary LanceDB instance for testing."""
    db = LanceDBManager()
    # Override the settings path
    original_path = settings.lancedb_path
    settings.lancedb_path = test_settings.lancedb_path
    settings.table_name = test_settings.table_name

    db.connect()
    db.get_or_create_table()

    yield db

    # Cleanup
    db.close()
    settings.lancedb_path = original_path
    settings.table_name = "chunks"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_document(tmp_path: Path) -> Path:
    """Create a sample document for testing."""
    doc_path = tmp_path / "sample.md"
    doc_path.write_text(
        """# Sample Document

This is a sample document for testing the knowledge base system.

## Section 1

This section contains information about vector databases.
Vector databases are specialized systems for storing and querying embeddings.

## Section 2

LanceDB is an open-source vector database that provides efficient similarity search.
It supports multiple index types and is optimized for machine learning workloads.

## Section 3

Semantic search uses embeddings to find relevant documents based on meaning.
This is different from keyword-based search which matches exact terms.
"""
    )
    return doc_path


@pytest.fixture
def sample_documents_dir(tmp_path: Path) -> Path:
    """Create a directory with multiple sample documents."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create multiple documents
    for i in range(3):
        doc = docs_dir / f"doc_{i}.txt"
        doc.write_text(f"Document {i} content.\nThis is test document number {i}.")

    # Create a subdirectory with more docs
    sub_dir = docs_dir / "subdir"
    sub_dir.mkdir()
    sub_doc = sub_dir / "nested.md"
    sub_doc.write_text("# Nested Document\n\nThis is a nested markdown file.")

    return docs_dir
