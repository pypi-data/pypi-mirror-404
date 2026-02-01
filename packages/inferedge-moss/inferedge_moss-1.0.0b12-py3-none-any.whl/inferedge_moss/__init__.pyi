from __future__ import annotations

from typing import ClassVar, Dict, List, Optional, Sequence


class MossClient:
    """Semantic search client for vector similarity operations."""

    def __init__(self, project_id: str, project_key: str) -> None:
        """Initialize the client.

        Args:
            project_id (str): Project identifier used for authentication.
            project_key (str): Project key used for authentication.
        """

    async def create_index(
        self,
        index_name: str,
        docs: List[DocumentInfo],
        model_id: Optional[str] = ...,
    ) -> bool:
        """Create a new index populated with documents.

        Args:
            index_name (str): Name of the index to create.
            docs (List[DocumentInfo]): Documents to ingest into the index.
            model_id (Optional[str]): Embedding model identifier to override the
                service default "moss-minilm".

        Returns:
            bool: True if the creation request succeeded.
        """

    async def get_index(self, index_name: str) -> IndexInfo:
        """Retrieve metadata for a single index.

        Args:
            index_name (str): Name of the index to inspect.

        Returns:
            IndexInfo: Metadata describing the requested index.
        """

    async def list_indexes(self) -> List[IndexInfo]:
        """List all indexes in the current project.

        Returns:
            List[IndexInfo]: Collection of index metadata objects.
        """

    async def delete_index(self, index_name: str) -> bool:
        """Delete an index and all associated documents.

        Args:
            index_name (str): Name of the index to delete.

        Returns:
            bool: True if the deletion request succeeded.
        """

    async def add_docs(
        self,
        index_name: str,
        docs: List[DocumentInfo],
        options: Optional[AddDocumentsOptions] = None,
    ) -> Dict[str, int]:
        """Insert or update documents in an index.

        Args:
            index_name (str): Target index name.
            docs (List[DocumentInfo]): Documents to add or upsert.
            options (Optional[AddDocumentsOptions]): Upsert behavior overrides.

        Returns:
            Dict[str, int]: Mutation counts such as inserted or updated totals.
        """

    async def delete_docs(self, index_name: str, doc_ids: List[str]) -> Dict[str, int]:
        """Remove documents by identifier.

        Args:
            index_name (str): Target index name.
            doc_ids (List[str]): Identifiers of documents to delete.

        Returns:
            Dict[str, int]: Summary counts for deleted documents.
        """

    async def get_docs(
        self,
        index_name: str,
        options: Optional[GetDocumentsOptions] = None,
    ) -> List[DocumentInfo]:
        """Fetch documents stored in an index.

        Args:
            index_name (str): Target index name.
            options (Optional[GetDocumentsOptions]): Retrieval filters.

        Returns:
            List[DocumentInfo]: Documents that satisfy the filters.
        """

    async def load_index(self, index_name: str) -> str:
        """Load an index from persistent storage.

        Args:
            index_name (str): Name of the index to load.

        Returns:
            str: Identifier or status describing the loaded index.
        """

    async def query(
        self,
        index_name: str,
        query: str,
        options: Optional[QueryOptions] = ...,
    ) -> SearchResult:
        """Execute a semantic similarity search.

        Args:
            index_name (str): Target index name.
            query (str): Natural language query string.
            options (Optional[QueryOptions]): Controls custom embeddings and per-query overrides.

        Returns:
            SearchResult: Ranked documents and metadata for the query.
        """

# Define types from moss_core (Rust extension module) inline
# since moss_core doesn't have its own .pyi stub file


class ModelRef:
    """Model identifier paired with a specific version string.
    
    Attributes:
        id: The model identifier (str).
        version: The model version string (str).
    """

    id: str
    version: str

    def __init__(self, id: str, version: str) -> None: ...


class QueryResultDocumentInfo:
    """A document returned from semantic search along with its similarity score.
    
    Attributes:
        id: The document identifier (str).
        text: The document text content (str).
        metadata: Optional dictionary of string key-value pairs for document metadata.
        score: The similarity score for this document (float, default 0.0).
    """

    id: str
    text: str
    metadata: Optional[Dict[str, str]]
    score: float

    def __init__(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, str]] = ...,
        score: float = ...,
    ) -> None: ...


class DocumentInfo:
    """Canonical representation of a document that can be added to a Moss index.
    
    Attributes:
        id: The document identifier (str).
        text: The document text content (str).
        metadata: Optional dictionary of string key-value pairs for document metadata.
    """

    id: str
    text: str
    metadata: Optional[Dict[str, str]]
    embedding: Optional[Sequence[float]]

    def __init__(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, str]] = ...,
        embedding: Optional[Sequence[float]] = ...,
    ) -> None: ...


class AddDocumentsOptions:
    """Options that control how documents are added to an index (for example upserts).
    
    Attributes:
        upsert: If True, existing document IDs will be overwritten; if False, duplicates will be skipped (bool, default True).
    """

    upsert: bool

    def __init__(self, upsert: bool = True) -> None: ...


class GetDocumentsOptions:
    """Options for retrieving documents, such as filtering by specific IDs.
    
    Attributes:
        doc_ids: Optional list of document IDs to filter by. If None, all documents are returned.
    """

    doc_ids: Optional[List[str]]

    def __init__(self, doc_ids: Optional[List[str]] = None) -> None: ...


class QueryOptions:
    """Optional parameters for semantic queries, including caller-provided embeddings."""

    embedding: Optional[Sequence[float]]
    top_k: Optional[int]
    alpha: Optional[float]

    def __init__(
        self,
        embedding: Optional[Sequence[float]] = ...,
        top_k: Optional[int] = ...,
        alpha: Optional[float] = ...,
    ) -> None: ...


class IndexInfo:
    """Metadata describing a Moss index, such as document counts and model bindings.
    
    Attributes:
        id: The index identifier (str).
        name: The index name (str).
        version: The index version string (str).
        status: The index status, one of "NotStarted", "Building", "Ready", or "Failed" (str).
        doc_count: The number of documents in the index (int).
        created_at: ISO 8601 timestamp of when the index was created (str).
        updated_at: ISO 8601 timestamp of when the index was last updated (str).
        model: The model reference associated with this index (ModelRef).
    """

    id: str
    name: str
    version: str
    status: str
    doc_count: int
    created_at: str
    updated_at: str
    model: ModelRef

    def __init__(
        self,
        id: str,
        name: str,
        version: str,
        status: str,
        doc_count: int,
        created_at: str,
        updated_at: str,
        model: ModelRef,
    ) -> None: ...


class SearchResult:
    """Results returned from semantic search, including ranked documents and metadata.
    
    Attributes:
        docs: List of ranked query result documents, ordered by relevance (List[QueryResultDocumentInfo]).
        query: The original search query string (str).
        index_name: Optional name of the index that was queried (Optional[str]).
        time_taken_ms: Optional time taken for the query in milliseconds (Optional[int]).
    """

    docs: List[QueryResultDocumentInfo]
    query: str
    index_name: Optional[str]
    time_taken_ms: Optional[int]

    def __init__(
        self,
        docs: List[QueryResultDocumentInfo],
        query: str,
        index_name: Optional[str] = None,
        time_taken_ms: Optional[int] = None,
    ) -> None: ...


class IndexStatus:
    """Index status enum values.
    
    Attributes:
        NotStarted: Index has not started building.
        Building: Index is currently being built.
        Ready: Index is ready for use.
        Failed: Index build failed.
    """

    NotStarted: ClassVar[str]
    Building: ClassVar[str]
    Ready: ClassVar[str]
    Failed: ClassVar[str]

    def __init__(self, value: str) -> None: ...


# IndexStatusValues is a dictionary mapping status names to their string values
IndexStatusValues: Dict[str, str]

__version__: str

__all__ = [
    "MossClient",
    # Core data types
    "DocumentInfo",
    "AddDocumentsOptions",
    "GetDocumentsOptions",
    "IndexInfo",
    "SearchResult",
    "QueryResultDocumentInfo",
    "ModelRef",
    "IndexStatus",
    "IndexStatusValues",
    "QueryOptions",
]