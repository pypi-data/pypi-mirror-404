# index_service.py
from __future__ import annotations

import sys
from typing import Dict, List, Literal, Optional, Sequence

from moss_core import Index  # PyO3-bound Rust class
from moss_core import (
    DocumentInfo,
    QueryOptions,
    SearchResult,
    SerializedIndex,
)

# Skip embedding service in Python 3.14
if sys.version_info < (3, 14):
    from .embedding_service import EmbeddingService
else:
    EmbeddingService = None  # type: ignore

MossModel = Literal["moss-minilm", "moss-mediumlm", "custom"]


class IndexService:
    def __init__(self) -> None:
        # In-memory registry of indices, backed by Rust via PyO3
        self._indexes: Dict[str, Index] = {}
        # Track the model id for each index so we can embed with the right model
        self._index_models: Dict[str, str] = {}
        # Cache embedding services by model ID to avoid repeated initialization
        self._embedding_services: Dict[str, EmbeddingService] = {}
        # Track known embedding dimensions per index for validation
        self._index_dimensions: Dict[str, Optional[int]] = {}

    async def _get_embedding_service(self, model_id: str) -> EmbeddingService:
        """Get or create an embedding service for the given model ID."""
        if sys.version_info >= (3, 14):
            raise RuntimeError(
                "Embedding service is not supported in Python 3.14. "
                "Please provide pre-computed embeddings via QueryOptions.embedding."
            )
        if model_id == "custom":
            raise ValueError(
                "Cannot create embedding service for 'custom' model. "
                "Custom model requires pre-computed embeddings to be provided."
            )
        if model_id not in self._embedding_services:
            embedding_service = EmbeddingService(
                model_id=model_id, normalize=True, quantized=False
            )
            await embedding_service.load_model()
            self._embedding_services[model_id] = embedding_service
        return self._embedding_services[model_id]

    # ---------- Index lifecycle ----------
    async def create_index_from_serialized(
        self, data: SerializedIndex, documents: List[DocumentInfo]
    ) -> Index:
        if data.name in self._indexes:
            raise ValueError(f"Index with name '{data.name}' already exists")

        # Construct with the serialized model id
        index = Index(data.name, data.model.id)
        # Rust deserialize is sync
        index.deserialize(data, documents)

        # Initialize embedding service for this model (skip for custom)
        if data.model.id != "custom" and sys.version_info < (3, 14):
            await self._get_embedding_service(data.model.id)

        actual_dimension = 0
        try:
            if hasattr(data, "embeddings") and data.embeddings:
                actual_dimension = len(data.embeddings[0]) if data.embeddings[0] else 0
        except Exception:
            actual_dimension = 0

        resolved_dimension = actual_dimension or (data.dimension if data.dimension > 0 else 0)

        self._indexes[data.name] = index
        self._index_models[data.name] = data.model.id
        self._index_dimensions[data.name] = resolved_dimension if resolved_dimension > 0 else None

        return index

    # ---------- Querying ----------

    async def query(self, index_name: str, query: str, options: QueryOptions) -> SearchResult:
        import time

        start_time = time.time()

        index = self._indexes.get(index_name)
        if not index:
            raise KeyError(f"Index '{index_name}' not found")

        model_str = self._index_models[index_name]

        raw_top_k = getattr(options, "top_k", None)
        if raw_top_k is None:
            resolved_top_k = 5
        else:
            try:
                resolved_top_k = int(raw_top_k)
            except (TypeError, ValueError) as error:
                raise ValueError("QueryOptions.top_k must be an integer value.") from error

            if resolved_top_k <= 0:
                resolved_top_k = 5
        resolved_alpha = options.alpha if getattr(options, "alpha", None) is not None else 0.8

        if options.embedding is None:
            if not query or query.strip() == "":
                raise ValueError(
                    "Query text or options.embedding must be provided for search operations."
                )
            # For custom model, embeddings must be provided
            if model_str == "custom":
                raise ValueError(
                    "This index was created with custom embeddings. Query embeddings must be provided via "
                    "QueryOptions.embedding. Automatic embedding generation is not supported for indexes with custom embeddings."
                )
            embedding_service = await self._get_embedding_service(model_str)
            q_emb = await embedding_service.create_embedding(query)
        else:
            q_emb = self._validate_embedding_vector(index_name, options.embedding)

        # Get raw query results from Rust (IDs and scores only)
        raw_result = index.query(query, resolved_top_k, q_emb, resolved_alpha)

        # Rust already returns full documents in result docs; no Python-side caching needed.
        populated_docs = []
        for result_doc in raw_result.docs:
            populated_doc = type(
                "QueryResultDoc",
                (),
                {
                    "id": result_doc.id,
                    "score": result_doc.score,
                    "text": result_doc.text,
                    "metadata": getattr(result_doc, "metadata", None),
                },
            )()
            populated_docs.append(populated_doc)

        # Calculate timing
        time_taken_ms = int((time.time() - start_time) * 1000)

        # Return SearchResult with populated documents
        return type(
            "SearchResult",
            (),
            {
                "docs": populated_docs,
                "query": query,
                "index_name": index_name,
                "time_taken_ms": time_taken_ms,
            },
        )()

    # ---------- Utilities ----------

    def has_index(self, index_name: str) -> bool:
        return index_name in self._indexes

    def _validate_embedding_vector(self, index_name: str, embedding: Sequence[float]) -> List[float]:
        if not isinstance(embedding, (list, tuple)):
            raise ValueError("Invalid embedding: expected a list or tuple of floats.")

        normalized: List[float] = []
        for value in embedding:
            if isinstance(value, (int, float)) and value == value and value not in (float("inf"), float("-inf")):
                normalized.append(float(value))
            else:
                raise ValueError("Invalid embedding: values must be finite numbers.")

        if not normalized:
            raise ValueError("Invalid embedding: vector cannot be empty.")

        stored_dimension = self._index_dimensions.get(index_name)
        if stored_dimension is not None and stored_dimension > 0:
            if len(normalized) != stored_dimension:
                raise ValueError(
                    f"Embedding dimension mismatch for index '{index_name}': "
                    f"expected {stored_dimension}, got {len(normalized)}."
                )
        else:
            self._index_dimensions[index_name] = len(normalized)

        return normalized