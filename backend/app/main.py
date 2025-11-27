"""FastAPI application with semantic knowledge base endpoints."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import db_manager
from app.models import (
    EncodeBatchRequest,
    EncodeBatchResponse,
    EncodeDocRequest,
    EncodeDocResponse,
    ErrorResponse,
    QueryRequest,
    QueryResponse,
    SearchResult,
)
from app.services import document_processor, model_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"LanceDB path: {settings.lancedb_uri}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"Reranker model: {settings.reranker_model}")

    # Initialize database connection
    db_manager.connect()
    db_manager.get_or_create_table()

    yield

    # Shutdown
    logger.info("Shutting down application")
    db_manager.close()


app = FastAPI(
    title=settings.app_name,
    description="Semantic Knowledge Base API with document ingestion and semantic search",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.post(
    "/encode_doc",
    response_model=EncodeDocResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid document format"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def encode_document(request: EncodeDocRequest) -> EncodeDocResponse:
    """Encode a single document into the knowledge base.

    Reads the document, chunks it semantically, generates embeddings,
    and stores the chunks in LanceDB.
    """
    logger.info(f"Encoding document: {request.file_path}")

    try:
        # Process document
        chunks, embeddings, offsets, token_counts = document_processor.process_document(
            request.file_path
        )

        if not chunks:
            return EncodeDocResponse(
                status="success",
                message="Document processed but no chunks generated (empty document)",
                document_path=request.file_path,
                chunk_count=0,
                token_counts=[],
            )

        # Store in database
        db_manager.add_chunks(
            contents=chunks,
            embeddings=embeddings,
            source_document=request.file_path,
            chunk_offsets=offsets,
            token_counts=token_counts,
        )

        return EncodeDocResponse(
            status="success",
            message=f"Successfully encoded document with {len(chunks)} chunks",
            document_path=request.file_path,
            chunk_count=len(chunks),
            token_counts=token_counts,
        )

    except FileNotFoundError as e:
        logger.error(f"Document not found: {request.file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except ValueError as e:
        logger.error(f"Invalid document: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception(f"Error encoding document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encode document: {str(e)}",
        ) from e


async def _process_batch_async(
    directory_path: str, file_patterns: list[str] | None
) -> None:
    """Background task to process documents in batch.

    Args:
        directory_path: Path to the directory.
        file_patterns: File patterns to match.
    """
    logger.info(f"Starting batch processing for: {directory_path}")

    try:
        documents = document_processor.discover_documents(directory_path, file_patterns)

        processed = 0
        failed = 0

        for doc_path in documents:
            try:
                chunks, embeddings, offsets, token_counts = (
                    document_processor.process_document(str(doc_path))
                )

                if chunks:
                    db_manager.add_chunks(
                        contents=chunks,
                        embeddings=embeddings,
                        source_document=str(doc_path),
                        chunk_offsets=offsets,
                        token_counts=token_counts,
                    )
                    processed += 1

            except Exception as e:
                logger.error(f"Failed to process {doc_path}: {e}")
                failed += 1

        logger.info(
            f"Batch processing complete: {processed} processed, {failed} failed"
        )

    except Exception as e:
        logger.exception(f"Batch processing failed: {e}")


@app.post(
    "/encode_batch",
    response_model=EncodeBatchResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Directory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def encode_batch(request: EncodeBatchRequest) -> EncodeBatchResponse:
    """Encode documents from a directory in batch.

    Discovers documents matching the specified patterns, processes them
    asynchronously in the background.
    """
    logger.info(f"Batch encoding from: {request.directory_path}")

    try:
        # Verify directory exists
        path = Path(request.directory_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {request.directory_path}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {request.directory_path}")

        # Discover documents to get count
        documents = document_processor.discover_documents(
            request.directory_path, request.file_patterns
        )

        if not documents:
            return EncodeBatchResponse(
                status="success",
                message="No documents found matching the specified patterns",
                documents_queued=0,
            )

        # Start background processing
        asyncio.create_task(
            _process_batch_async(request.directory_path, request.file_patterns)
        )

        return EncodeBatchResponse(
            status="success",
            message=f"Batch processing started for {len(documents)} documents",
            documents_queued=len(documents),
        )

    except FileNotFoundError as e:
        logger.error(f"Directory not found: {request.directory_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except ValueError as e:
        logger.error(f"Invalid path: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception(f"Error starting batch processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch processing: {str(e)}",
        ) from e


@app.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def query(request: QueryRequest) -> QueryResponse:
    """Perform semantic search on the knowledge base.

    Generates a query embedding, performs vector search in LanceDB,
    and reranks results using the reranker model.
    """
    logger.info(f"Query: {request.query[:50]}...")

    try:
        # Generate query embedding
        query_embedding = model_manager.encode_query(request.query)

        # Perform vector search
        candidates = db_manager.vector_search(
            query_embedding, limit=settings.vector_search_limit
        )

        if not candidates:
            return QueryResponse(
                status="success",
                message="No results found",
                results=[],
                query=request.query,
            )

        # Extract documents for reranking
        documents = [c["content"] for c in candidates]

        # Rerank results
        reranked = model_manager.rerank(request.query, documents, top_k=request.top_k)

        # Build results
        results = [
            SearchResult(
                content=candidates[idx]["content"],
                relevance_score=float(score),
                source_document=candidates[idx]["source_document"],
                chunk_offset=candidates[idx]["chunk_offset"],
            )
            for idx, score in reranked
        ]

        return QueryResponse(
            status="success",
            message=f"Found {len(results)} results",
            results=results,
            query=request.query,
        )

    except Exception as e:
        logger.exception(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}",
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
