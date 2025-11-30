"""Custom exceptions for the knowledge base API."""


class IndexNotFoundError(Exception):
    """Raised when a specified index does not exist."""

    def __init__(self, index_name: str) -> None:
        """Initialize with index name."""
        self.index_name = index_name
        super().__init__(f"Index not found: {index_name}")


class IndexAlreadyExistsError(Exception):
    """Raised when attempting to create an index that already exists."""

    def __init__(self, index_name: str) -> None:
        """Initialize with index name."""
        self.index_name = index_name
        super().__init__(f"Index already exists: {index_name}")


class DocumentNotFoundError(Exception):
    """Raised when a document file is not found."""

    def __init__(self, document_path: str) -> None:
        """Initialize with document path."""
        self.document_path = document_path
        super().__init__(f"Document not found: {document_path}")


class DirectoryNotFoundError(Exception):
    """Raised when a directory path is not found."""

    def __init__(self, directory_path: str) -> None:
        """Initialize with directory path."""
        self.directory_path = directory_path
        super().__init__(f"Directory not found: {directory_path}")


class InvalidIndexNameError(Exception):
    """Raised when an index name does not match the required pattern."""

    def __init__(self, index_name: str) -> None:
        """Initialize with invalid index name."""
        self.index_name = index_name
        super().__init__(
            f"Invalid index name: '{index_name}'. "
            "Must start with a letter and contain only alphanumeric characters, "
            "underscores, or hyphens.",
        )


class LLMSTxtFetchError(Exception):
    """Raised when fetching llms.txt or markdown content fails."""

    def __init__(self, url: str, reason: str) -> None:
        """Initialize with URL and failure reason."""
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch '{url}': {reason}")


class LLMSTxtParseError(Exception):
    """Raised when parsing llms.txt content fails."""

    def __init__(self, url: str, reason: str) -> None:
        """Initialize with URL and parse error reason."""
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to parse llms.txt from '{url}': {reason}")
