"""Document processing services: chunking, embedding, and reranking."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import semchunk
from loguru import logger
from sentence_transformers import CrossEncoder, SentenceTransformer

from app.config import settings
from app.exceptions import (
    DirectoryNotFoundError,
    DocumentNotFoundError,
    LLMSTxtFetchError,
    LLMSTxtParseError,
)

# =============================================================================
# Type Aliases (PEP 695 - Python 3.12+)
# =============================================================================

# Embedding types
type Embedding = list[float]
type EmbeddingBatch = list[Embedding]

# Document processing result types
type ChunkOffsets = list[int]
type TokenCounts = list[int]
type ChunkResult = tuple[list[str], ChunkOffsets]
type DocumentResult = tuple[list[str], EmbeddingBatch, ChunkOffsets, TokenCounts]

# Reranking result: list of (index, score) tuples
type RerankResult = list[tuple[int, float]]


class ModelManager:
    """Manages ML models for embedding and reranking."""

    def __init__(self) -> None:
        """Initialize the model manager with lazy loading."""
        self._embedding_model: SentenceTransformer | None = None
        self._reranker_model: CrossEncoder | None = None
        self._tokenizer = None

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load and return the embedding model."""
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._embedding_model = SentenceTransformer(
                settings.embedding_model,
                trust_remote_code=True,
            )
            logger.info(
                f"Embedding model loaded. Dimension: {self._embedding_model.get_sentence_embedding_dimension()}",
            )
        return self._embedding_model

    @property
    def reranker_model(self) -> CrossEncoder:
        """Lazy load and return the reranker model."""
        if self._reranker_model is None:
            logger.info(f"Loading reranker model: {settings.reranker_model}")
            self._reranker_model = CrossEncoder(
                settings.reranker_model,
                trust_remote_code=True,
            )
            logger.info("Reranker model loaded")
        return self._reranker_model

    @property
    def tokenizer(self):
        """Get the tokenizer from the embedding model."""
        if self._tokenizer is None:
            self._tokenizer = self.embedding_model.tokenizer
        return self._tokenizer

    def encode(self, texts: list[str]) -> EmbeddingBatch:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to encode.

        Returns:
            List of embedding vectors (768-dim each).

        """
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def encode_query(self, query: str) -> Embedding:
        """
        Generate embedding for a query.

        Args:
            query: Query text.

        Returns:
            Embedding vector (768-dim).

        """
        embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        return embedding.tolist()

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> RerankResult:
        """
        Rerank documents based on relevance to query.

        Args:
            query: Query text.
            documents: List of document texts to rerank.
            top_k: Number of top results to return.

        Returns:
            List of (index, score) tuples sorted by relevance.

        """
        if not documents:
            return []

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get relevance scores
        scores = self.reranker_model.predict(pairs)

        # Create index-score pairs and sort by score descending
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        return indexed_scores[:top_k]

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text using the embedding model's tokenizer.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens.

        """
        return len(self.tokenizer.encode(text))


# Global model manager instance
model_manager = ModelManager()


class DocumentProcessor:
    """Processes documents: reading, chunking, and encoding."""

    def __init__(self, model_manager: ModelManager) -> None:
        """Initialize with a model manager."""
        self.model_manager = model_manager
        self._chunker = None

    @property
    def chunker(self):
        """Lazy load the semantic chunker."""
        if self._chunker is None:
            # Create chunker using the model's tokenizer
            self._chunker = semchunk.chunkerify(
                self.model_manager.tokenizer,
                chunk_size=settings.max_chunk_tokens,
            )
        return self._chunker

    def read_document(self, file_path: str) -> str:
        """
        Read document content from file.

        Args:
            file_path: Path to the document file.

        Returns:
            Document content as string.

        Raises:
            DocumentNotFoundError: If file doesn't exist.
            ValueError: If path is not a file.

        """
        path = Path(file_path)

        if not path.exists():
            raise DocumentNotFoundError(file_path)

        if not path.is_file():
            msg = f"Path is not a file: {file_path}"
            raise ValueError(msg)

        logger.debug(f"Reading document: {file_path}")
        return path.read_text(encoding="utf-8")

    def chunk_document(self, content: str) -> ChunkResult:
        """
        Split document into semantic chunks.

        Args:
            content: Document content.

        Returns:
            Tuple of (chunks, offsets) where offsets are character positions.

        """
        chunks = self.chunker(content)

        # Calculate character offsets for each chunk
        offsets = []
        current_offset = 0
        for chunk in chunks:
            # Find the chunk in the content starting from current position
            idx = content.find(chunk, current_offset)
            if idx != -1:
                offsets.append(idx)
                current_offset = idx + len(chunk)
            else:
                # Fallback: use current offset if exact match not found
                offsets.append(current_offset)
                current_offset += len(chunk)

        logger.debug(f"Document chunked into {len(chunks)} chunks")
        return chunks, offsets

    def process_document(
        self,
        file_path: str,
    ) -> DocumentResult:
        """
        Process a document: read, chunk, and generate embeddings.

        Args:
            file_path: Path to the document file.

        Returns:
            Tuple of (chunks, embeddings, offsets, token_counts).

        """
        # Read document
        content = self.read_document(file_path)

        # Chunk document
        chunks, offsets = self.chunk_document(content)

        if not chunks:
            logger.warning(f"No chunks generated for document: {file_path}")
            return [], [], [], []

        # Generate embeddings
        embeddings = self.model_manager.encode(chunks)

        # Count tokens for each chunk
        token_counts = [self.model_manager.count_tokens(chunk) for chunk in chunks]

        logger.info(
            f"Processed {file_path}: {len(chunks)} chunks, token counts: {token_counts}",
        )

        return chunks, embeddings, offsets, token_counts

    def discover_documents(
        self,
        directory_path: str,
        patterns: list[str] | None = None,
    ) -> list[Path]:
        """
        Discover documents in a directory matching patterns.

        Args:
            directory_path: Path to the directory.
            patterns: File patterns to match (e.g., ['*.txt', '*.md']).

        Returns:
            List of discovered document paths.

        Raises:
            DirectoryNotFoundError: If directory doesn't exist.
            ValueError: If path is not a directory.

        """
        path = Path(directory_path)

        if not path.exists():
            raise DirectoryNotFoundError(directory_path)

        if not path.is_dir():
            msg = f"Path is not a directory: {directory_path}"
            raise ValueError(msg)

        patterns = patterns or settings.default_file_patterns
        documents = []

        for pattern in patterns:
            documents.extend(path.rglob(pattern))

        # Remove duplicates and sort
        documents = sorted(set(documents))

        logger.info(
            f"Discovered {len(documents)} documents in {directory_path} "
            f"matching patterns: {patterns}",
        )

        return documents


# Global document processor instance
document_processor = DocumentProcessor(model_manager)


# =============================================================================
# Type Aliases for LLMSTxtScraper
# =============================================================================

# Parsed llms.txt structure: {section_name: [(title, url, description), ...]}
type ParsedLLMSTxt = dict[str, list[tuple[str, str, str]]]

# Fetch result: (url, content) or (url, None) on failure
type FetchResult = tuple[str, str | None]


class LLMSTxtScraper:
    """Service for fetching and parsing llms.txt files and downloading markdown content."""

    # Regex pattern for markdown links: [title](url) with optional description
    LINK_PATTERN = re.compile(r"-\s*\[([^\]]+)\]\(([^)]+)\)(?::\s*(.+))?")
    # Regex pattern for section headers (## Section Name)
    SECTION_PATTERN = re.compile(r"^##\s+(.+)$", re.MULTILINE)

    def __init__(
        self,
        model_manager: ModelManager,
        max_concurrent: int = 10,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the LLMSTxtScraper.

        Args:
            model_manager: ModelManager instance for embedding/chunking.
            max_concurrent: Maximum concurrent HTTP connections.
            timeout: HTTP request timeout in seconds.

        """
        self.model_manager = model_manager
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=self.max_concurrent,
                    max_keepalive_connections=5,
                ),
                headers={
                    "User-Agent": "SimpleKnowledgeBase/1.0 (llms.txt scraper)",
                    "Accept": "text/plain, text/markdown, */*",
                },
            )
        return self._client

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._semaphore = None

    async def fetch_url(self, url: str) -> str:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch.

        Returns:
            Response text content.

        Raises:
            LLMSTxtFetchError: If fetch fails.

        """
        client = await self.get_client()
        try:
            async with self.semaphore:
                logger.debug(f"Fetching: {url}")
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            raise LLMSTxtFetchError(url, f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise LLMSTxtFetchError(url, str(e)) from e

    async def fetch_markdown_safe(self, url: str) -> FetchResult:
        """
        Fetch markdown content from URL, returning None on failure.

        Args:
            url: URL to fetch.

        Returns:
            Tuple of (url, content) or (url, None) on failure.

        """
        try:
            content = await self.fetch_url(url)
        except LLMSTxtFetchError as e:
            logger.warning(f"Failed to fetch markdown: {e}")
            return url, None
        else:
            return url, content

    def parse_llms_txt(self, content: str, base_url: str) -> ParsedLLMSTxt:
        """
        Parse llms.txt content and extract markdown URLs organized by section.

        Args:
            content: Raw llms.txt content.
            base_url: Base URL for resolving relative links.

        Returns:
            Dictionary mapping section names to list of (title, url, description) tuples.

        Raises:
            LLMSTxtParseError: If no links found in content.

        """
        result: ParsedLLMSTxt = {}
        current_section = "default"

        # Parse base URL for resolving relative links
        parsed_base = urlparse(base_url)
        base_for_relative = f"{parsed_base.scheme}://{parsed_base.netloc}"

        for raw_line in content.split("\n"):
            line = raw_line.strip()

            # Check for section header
            section_match = self.SECTION_PATTERN.match(line)
            if section_match:
                current_section = section_match.group(1).strip()
                if current_section not in result:
                    result[current_section] = []
                continue

            # Check for markdown link
            link_match = self.LINK_PATTERN.match(line)
            if link_match:
                title = link_match.group(1).strip()
                url = link_match.group(2).strip()
                description = link_match.group(3).strip() if link_match.group(3) else ""

                # Resolve relative URLs
                if not url.startswith(("http://", "https://")):
                    url = urljoin(base_for_relative, url)

                # Only include markdown files
                if url.endswith(".md") or ".md#" in url:
                    # Remove anchor for fetching
                    fetch_url = url.split("#")[0]

                    if current_section not in result:
                        result[current_section] = []
                    result[current_section].append((title, fetch_url, description))

        # Check if any links were found
        total_links = sum(len(links) for links in result.values())
        if total_links == 0:
            raise LLMSTxtParseError(base_url, "No markdown links found in llms.txt")

        logger.info(
            f"Parsed llms.txt: {len(result)} sections, {total_links} markdown links",
        )
        return result

    def filter_sections(
        self,
        parsed: ParsedLLMSTxt,
        sections: list[str] | None,
    ) -> ParsedLLMSTxt:
        """
        Filter parsed content to include only specified sections.

        Args:
            parsed: Parsed llms.txt structure.
            sections: Section names to include, or None for all.

        Returns:
            Filtered ParsedLLMSTxt with only requested sections.

        """
        if sections is None:
            return parsed

        return {
            section: links for section, links in parsed.items() if section in sections
        }

    def get_unique_urls(self, parsed: ParsedLLMSTxt) -> list[str]:
        """
        Extract unique URLs from parsed llms.txt.

        Args:
            parsed: Parsed llms.txt structure.

        Returns:
            List of unique URLs.

        """
        urls = set()
        for links in parsed.values():
            for _, url, _ in links:
                urls.add(url)
        return list(urls)

    async def fetch_all_markdown(
        self,
        urls: list[str],
    ) -> dict[str, str]:
        """
        Fetch all markdown content concurrently.

        Args:
            urls: List of URLs to fetch.

        Returns:
            Dictionary mapping URL to content (only successful fetches).

        """
        logger.info(f"Fetching {len(urls)} markdown files...")

        tasks = [self.fetch_markdown_safe(url) for url in urls]
        results = await asyncio.gather(*tasks)

        # Filter out failed fetches
        content_map = {url: content for url, content in results if content is not None}

        success_count = len(content_map)
        fail_count = len(urls) - success_count
        logger.info(f"Fetched {success_count} files, {fail_count} failed")

        return content_map

    async def process_llms_txt(
        self,
        llms_txt_url: str,
        index_name: str,
        sections: list[str] | None = None,
        db_manager=None,
    ) -> tuple[int, list[str]]:
        """
        Main processing method: fetch, parse, download, and ingest documents.

        Args:
            llms_txt_url: URL to the llms.txt file.
            index_name: Target index name for storage.
            sections: Optional list of section names to filter.
            db_manager: LanceDBManager instance for storage.

        Returns:
            Tuple of (documents_processed, sections_found).

        Raises:
            LLMSTxtFetchError: If llms.txt cannot be fetched.
            LLMSTxtParseError: If llms.txt cannot be parsed.

        """
        # Import here to avoid circular import
        if db_manager is None:
            from app.database import db_manager as _db_manager

            db_manager = _db_manager

        # Step 1: Fetch llms.txt
        logger.info(f"Fetching llms.txt from: {llms_txt_url}")
        llms_txt_content = await self.fetch_url(llms_txt_url)

        # Step 2: Parse llms.txt
        parsed = self.parse_llms_txt(llms_txt_content, llms_txt_url)
        sections_found = list(parsed.keys())

        # Step 3: Filter sections if specified
        if sections:
            parsed = self.filter_sections(parsed, sections)
            logger.info(f"Filtered to {len(parsed)} sections: {list(parsed.keys())}")

        # Step 4: Get unique URLs
        urls = self.get_unique_urls(parsed)
        if not urls:
            logger.warning("No URLs to process after filtering")
            return 0, sections_found

        # Step 5: Fetch all markdown content
        content_map = await self.fetch_all_markdown(urls)

        # Step 6: Process and store documents
        documents_processed = 0
        doc_processor = DocumentProcessor(self.model_manager)

        for url, content in content_map.items():
            try:
                # Chunk the content
                chunks, offsets = doc_processor.chunk_document(content)

                if not chunks:
                    logger.debug(f"No chunks generated for: {url}")
                    continue

                # Generate embeddings
                embeddings = self.model_manager.encode(chunks)

                # Count tokens
                token_counts = [
                    self.model_manager.count_tokens(chunk) for chunk in chunks
                ]

                # Store in database
                db_manager.add_chunks(
                    index_name=index_name,
                    contents=chunks,
                    embeddings=embeddings,
                    source_document=url,
                    chunk_offsets=offsets,
                    token_counts=token_counts,
                )

                documents_processed += 1
                logger.debug(f"Processed {url}: {len(chunks)} chunks")

            except Exception:  # noqa: BLE001
                logger.exception(f"Failed to process document: {url}")

        logger.info(
            f"llms.txt ingestion complete: {documents_processed}/{len(content_map)} documents processed",
        )
        return documents_processed, sections_found


# Global LLMSTxt scraper instance
llms_txt_scraper = LLMSTxtScraper(model_manager)
