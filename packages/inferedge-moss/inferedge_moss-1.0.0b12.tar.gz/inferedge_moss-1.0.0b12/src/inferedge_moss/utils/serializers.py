"""
Serialization utilities for converting between Python objects and cloud API data formats.
"""

from typing import Dict, List, Optional

from moss_core import DocumentInfo, IndexInfo, ModelRef, QueryResultDocumentInfo, SearchResult


class CloudApiSerializer:
    """
    Handles serialization and conversion between Python objects and cloud API formats.
    The cloud API uses camelCase field names while Python objects use snake_case.
    """

    @staticmethod
    def serialize_document(doc: DocumentInfo) -> dict:
        """Convert DocumentInfo to dictionary for JSON serialization."""
        try:
            # Try to access attributes directly (PyO3 class)
            doc_dict = {
                "id": doc.id,
                "text": doc.text,
            }
            # Add metadata if it exists (optional field)
            if hasattr(doc, "metadata") and doc.metadata is not None:
                doc_dict["metadata"] = doc.metadata
            if hasattr(doc, "embedding") and doc.embedding is not None:
                embedding = doc.embedding
                if not isinstance(embedding, (list, tuple)):
                    raise ValueError("Document embedding must be a list or tuple of floats.")
                doc_dict["embedding"] = [float(value) for value in embedding]
            return doc_dict
        except AttributeError:
            # Fallback to dict conversion if available
            if hasattr(doc, "__dict__"):
                return doc.__dict__
            else:
                # Last resort - assume it's already a dict
                return doc

    @staticmethod
    def serialize_options(options) -> Optional[dict]:
        """Convert options object to dictionary for JSON serialization."""
        if options is None:
            return None
        try:
            # Handle PyO3 classes from Rust - convert to camelCase for cloud API
            if hasattr(options, "__class__") and options.__class__.__name__ in [
                "GetDocumentsOptions",
                "AddDocumentsOptions",
                "QueryOptions",
            ]:
                result = {}
                # Extract attributes based on the options type
                if options.__class__.__name__ == "GetDocumentsOptions":
                    if hasattr(options, "doc_ids"):
                        result["docIds"] = (
                            options.doc_ids
                        )  # Convert snake_case to camelCase
                elif options.__class__.__name__ == "AddDocumentsOptions":
                    if hasattr(options, "upsert"):
                        result["upsert"] = options.upsert
                elif options.__class__.__name__ == "QueryOptions":
                    if hasattr(options, "embedding") and options.embedding is not None:
                        result["embedding"] = [
                            float(value) for value in options.embedding
                        ]
                    if hasattr(options, "top_k") and options.top_k is not None:
                        result["topK"] = int(options.top_k)
                    if hasattr(options, "alpha") and options.alpha is not None:
                        result["alpha"] = float(options.alpha)
                return result
            elif hasattr(options, "__dict__"):
                return options.__dict__
            else:
                # Assume it's already a dict
                return options
        except:
            return None

    @staticmethod
    def dict_to_index_info(data: dict) -> IndexInfo:
        """Convert dictionary from cloud API to IndexInfo object."""
        # Create ModelRef from model data
        model_data = data.get("model", {})
        model_id = model_data.get("id") if model_data else None
        model_version = model_data.get("version") if model_data else None

        # Ensure all strings are not None
        model = ModelRef(id=model_id or "unknown", version=model_version or "unknown")

        # Create IndexInfo with all required parameters, ensuring no None values
        # Cloud API uses camelCase field names
        return IndexInfo(
            id=data.get("id") or "",
            name=data.get("name") or "",
            version=data.get("version") or "",
            status=data.get("status") or "",
            doc_count=int(data.get("docCount", 0)),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
            model=model,
        )

    @staticmethod
    def convert_documents_response(response) -> List[DocumentInfo]:
        """Convert cloud API response to list of DocumentInfo objects."""
        if isinstance(response, list):
            document_infos = []
            for doc_data in response:
                if isinstance(doc_data, dict):
                    # Create DocumentInfo from dictionary (handles potential camelCase fields)
                    doc_info = DocumentInfo(
                        id=doc_data["id"],
                        text=doc_data["text"],
                        metadata=doc_data.get("metadata"),  # Optional field
                        embedding=doc_data.get("embedding"),
                    )
                    document_infos.append(doc_info)
                else:
                    # Already a DocumentInfo object
                    document_infos.append(doc_data)
            return document_infos

        return response

    @staticmethod
    def dict_to_search_result(data: dict) -> SearchResult:
        docs = []
        for doc_data in data.get("docs", []):
            doc = QueryResultDocumentInfo(
                id=doc_data.get("id", ""),
                text=doc_data.get("text", ""),
                metadata=doc_data.get("metadata"),
                score=float(doc_data.get("score", 0.0)),
            )
            docs.append(doc)

        return SearchResult(
            docs=docs,
            query=data.get("query", ""),
            index_name=data.get("indexName"),
            time_taken_ms=data.get("timeTakenMs"),
        )
