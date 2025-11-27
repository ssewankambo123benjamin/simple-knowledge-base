"""LanceDB database connection and operations."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

import lancedb
from lancedb.table import Table
from loguru import logger

from app.config import settings
from app.models import ChunkSchema


class LanceDBManager:
    """Manager for LanceDB operations."""

    def __init__(self) -> None:
        """Initialize the database manager."""
        self._db: Optional[lancedb.DBConnection] = None
        self._table: Optional[Table] = None

    def connect(self) -> lancedb.DBConnection:
        """Establish connection to LanceDB.

        Returns:
            LanceDB connection instance.
        """
        if self._db is None:
            logger.info(f"Connecting to LanceDB at {settings.lancedb_uri}")
            settings.lancedb_uri.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(settings.lancedb_uri)
            logger.info("LanceDB connection established")
        return self._db

    def get_or_create_table(self) -> Table:
        """Get existing table or create a new one.

        Returns:
            LanceDB table instance.
        """
        if self._table is not None:
            return self._table

        db = self.connect()

        if settings.table_name in db.table_names():
            logger.info(f"Opening existing table: {settings.table_name}")
            self._table = db.open_table(settings.table_name)
        else:
            logger.info(f"Creating new table: {settings.table_name}")
            self._table = db.create_table(settings.table_name, schema=ChunkSchema)

        return self._table

    def add_chunks(
        self,
        contents: list[str],
        embeddings: list[list[float]],
        source_document: str,
        chunk_offsets: list[int],
        token_counts: list[int],
    ) -> int:
        """Add chunks with embeddings to the database.

        Args:
            contents: List of chunk text contents.
            embeddings: List of embedding vectors (768-dim each).
            source_document: Source document identifier.
            chunk_offsets: Character offsets for each chunk.
            token_counts: Token counts for each chunk.

        Returns:
            Number of chunks added.
        """
        table = self.get_or_create_table()

        chunks = [
            ChunkSchema(
                chunk_id=str(uuid4()),
                content=content,
                embedding=embedding,
                source_document=source_document,
                chunk_offset=offset,
                token_count=token_count,
                created_at=datetime.now(),
            )
            for content, embedding, offset, token_count in zip(
                contents, embeddings, chunk_offsets, token_counts, strict=True
            )
        ]

        table.add([chunk.model_dump() for chunk in chunks])
        logger.info(f"Added {len(chunks)} chunks from {source_document}")

        return len(chunks)

    def vector_search(
        self, query_embedding: list[float], limit: int = 20
    ) -> list[dict]:
        """Perform vector similarity search.

        Args:
            query_embedding: Query embedding vector (768-dim).
            limit: Maximum number of results to return.

        Returns:
            List of matching chunks with scores.
        """
        table = self.get_or_create_table()

        results = table.search(query_embedding).limit(limit).to_list()

        logger.debug(f"Vector search returned {len(results)} candidates")
        return results

    def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            logger.info("Closing LanceDB connection")
            self._db = None
            self._table = None


# Global database manager instance
db_manager = LanceDBManager()
