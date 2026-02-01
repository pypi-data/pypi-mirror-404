"""
End-to-End tests for MossClient with cloud API

Prerequisites:
- Set MOSS_TEST_PROJECT_ID environment variable
- Set MOSS_TEST_PROJECT_KEY environment variable
- Ensure cloud API is accessible
"""

from __future__ import annotations

import os
import sys
import warnings

import pytest
import pytest_asyncio

from inferedge_moss import (
    AddDocumentsOptions,
    DocumentInfo,
    GetDocumentsOptions,
    MossClient,
    QueryOptions,
)
from tests.constants import (
    ADDITIONAL_TEST_DOCUMENTS,
    TEST_DOCUMENTS,
    TEST_MODEL_ID,
    TEST_PROJECT_ID,
    TEST_PROJECT_KEY,
    TEST_QUERIES,
    generate_unique_index_name,
)

# Skip embedding service in Python 3.14
if sys.version_info < (3, 14):
    from inferedge_moss.services.embedding_service import EmbeddingService
else:
    EmbeddingService = None  # type: ignore


@pytest.fixture(scope="module")
def moss_client():
    """Create a MossClient for the test module."""
    if not os.getenv("MOSS_TEST_PROJECT_ID") or not os.getenv("MOSS_TEST_PROJECT_KEY"):
        warnings.warn(
            "Warning: Using default test credentials. Set MOSS_TEST_PROJECT_ID and "
            "MOSS_TEST_PROJECT_KEY env vars for actual testing."
        )
    return MossClient(TEST_PROJECT_ID, TEST_PROJECT_KEY)


class TestMossClientE2E:
    """End-to-End tests for MossClient with cloud API."""

    class TestIndexLifecycle:
        """Test index lifecycle operations."""

        @pytest.mark.asyncio
        async def test_list_indexes_successfully(self, moss_client):
            """Should list indexes successfully."""
            indexes = await moss_client.list_indexes()

            assert isinstance(indexes, list)

            # Verify structure of index info
            if len(indexes) > 0:
                first_index = indexes[0]
                assert hasattr(first_index, "name")
                assert hasattr(first_index, "doc_count")
                assert hasattr(first_index, "model")

        @pytest.mark.asyncio
        async def test_create_and_retrieve_index(self, moss_client):
            """Should create a new index with documents and retrieve its info."""
            index_name = generate_unique_index_name("test-create")

            try:
                # Create the index
                docs = [
                    DocumentInfo(id=doc["id"], text=doc["text"])
                    for doc in TEST_DOCUMENTS
                ]
                success = await moss_client.create_index(
                    index_name, docs, TEST_MODEL_ID
                )
                assert success is True

                # Retrieve index information
                index_info = await moss_client.get_index(index_name)
                assert index_info.name == index_name
                assert index_info.doc_count == len(TEST_DOCUMENTS)
                assert index_info.model.id == TEST_MODEL_ID

                # Verify duplicate creation fails
                with pytest.raises(Exception):
                    await moss_client.create_index(index_name, docs, TEST_MODEL_ID)

            finally:
                # Cleanup: delete the index
                try:
                    await moss_client.delete_index(index_name)
                except Exception:
                    pass

        @pytest.mark.asyncio
        async def test_fail_get_nonexistent_index(self, moss_client):
            """Should fail to get non-existent index."""
            with pytest.raises(Exception):
                await moss_client.get_index("non-existent-index")

    class TestDocumentOperations:
        """Test document operations."""

        @pytest_asyncio.fixture
        async def index_with_docs(self, moss_client):
            """Create an index with documents and clean up after tests."""
            index_name = generate_unique_index_name("test-docs")

            # Create the index with initial documents
            docs = [
                DocumentInfo(id=doc["id"], text=doc["text"]) for doc in TEST_DOCUMENTS
            ]
            await moss_client.create_index(index_name, docs, TEST_MODEL_ID)

            yield index_name

            # Cleanup: delete the index
            try:
                await moss_client.delete_index(index_name)
            except Exception:
                pass

        @pytest.mark.asyncio
        async def test_retrieve_documents_from_index(self, moss_client, index_with_docs):
            """Should retrieve documents from index."""
            docs = await moss_client.get_docs(index_with_docs)

            assert len(docs) == len(TEST_DOCUMENTS)

            # Verify document structure
            for doc in docs:
                assert hasattr(doc, "id")
                assert hasattr(doc, "text")
                assert isinstance(doc.id, str)
                assert isinstance(doc.text, str)

            # Verify all test documents are present
            doc_ids = [doc.id for doc in docs]
            for test_doc in TEST_DOCUMENTS:
                assert test_doc["id"] in doc_ids

        @pytest.mark.asyncio
        async def test_retrieve_specific_documents_by_id(
            self, moss_client, index_with_docs
        ):
            """Should retrieve specific documents by ID."""
            target_doc_ids = ["doc-1", "doc-3"]
            docs = await moss_client.get_docs(
                index_with_docs, GetDocumentsOptions(doc_ids=target_doc_ids)
            )

            assert len(docs) == len(target_doc_ids)

            retrieved_ids = [doc.id for doc in docs]
            for doc_id in target_doc_ids:
                assert doc_id in retrieved_ids

        @pytest.mark.asyncio
        async def test_add_new_documents_to_existing_index(
            self, moss_client, index_with_docs
        ):
            """Should add new documents to existing index."""
            additional_docs = [
                DocumentInfo(id=doc["id"], text=doc["text"])
                for doc in ADDITIONAL_TEST_DOCUMENTS
            ]

            result = await moss_client.add_docs(index_with_docs, additional_docs)

            assert result["added"] == len(ADDITIONAL_TEST_DOCUMENTS)
            assert result.get("updated", 0) == 0

            # Verify documents were added
            index_info = await moss_client.get_index(index_with_docs)
            assert index_info.doc_count == len(TEST_DOCUMENTS) + len(
                ADDITIONAL_TEST_DOCUMENTS
            )

        @pytest.mark.asyncio
        async def test_update_existing_documents_with_upsert(
            self, moss_client, index_with_docs
        ):
            """Should update existing documents with upsert."""
            updated_doc = DocumentInfo(
                id="doc-1",
                text="Updated: Machine learning is a powerful subset of artificial intelligence with modern applications.",
            )

            result = await moss_client.add_docs(
                index_with_docs, [updated_doc], AddDocumentsOptions(upsert=True)
            )

            assert result.get("added", 0) == 0
            assert result["updated"] == 1

            # Verify document was updated
            docs = await moss_client.get_docs(
                index_with_docs, GetDocumentsOptions(doc_ids=["doc-1"])
            )
            assert docs[0].text == updated_doc.text

        @pytest.mark.asyncio
        async def test_delete_documents_from_index(self, moss_client, index_with_docs):
            """Should delete documents from index."""
            # First add the additional docs so we can delete them
            additional_docs = [
                DocumentInfo(id=doc["id"], text=doc["text"])
                for doc in ADDITIONAL_TEST_DOCUMENTS
            ]
            await moss_client.add_docs(index_with_docs, additional_docs)

            # Now delete them
            docs_to_delete = ["doc-6", "doc-7"]
            result = await moss_client.delete_docs(index_with_docs, docs_to_delete)

            assert result["deleted"] == len(docs_to_delete)

            # Verify documents were deleted
            remaining_docs = await moss_client.get_docs(index_with_docs)
            remaining_ids = [doc.id for doc in remaining_docs]

            for doc_id in docs_to_delete:
                assert doc_id not in remaining_ids

    class TestSearchAndQuery:
        """Test search and query operations."""

        @pytest_asyncio.fixture
        async def loaded_index(self, moss_client):
            """Create an index, load it, and clean up after tests."""
            index_name = generate_unique_index_name("test-query")

            # Create the index with documents
            docs = [
                DocumentInfo(id=doc["id"], text=doc["text"]) for doc in TEST_DOCUMENTS
            ]
            await moss_client.create_index(index_name, docs, TEST_MODEL_ID)

            # Load the index
            await moss_client.load_index(index_name)

            yield index_name

            # Cleanup: delete the index
            try:
                await moss_client.delete_index(index_name)
            except Exception:
                pass

        @pytest.mark.skipif(
            sys.version_info >= (3, 14),
            reason="Requires EmbeddingService for local query (not available in Python 3.14)",
        )
        @pytest.mark.asyncio
        async def test_load_index_successfully(self, moss_client):
            """Should load index successfully."""
            index_name = generate_unique_index_name("test-load")

            try:
                # Create the index
                docs = [
                    DocumentInfo(id=doc["id"], text=doc["text"])
                    for doc in TEST_DOCUMENTS
                ]
                await moss_client.create_index(index_name, docs, TEST_MODEL_ID)

                # Load the index
                loaded_index_name = await moss_client.load_index(index_name)
                assert loaded_index_name == index_name
            finally:
                try:
                    await moss_client.delete_index(index_name)
                except Exception:
                    pass

        @pytest.mark.skipif(
            sys.version_info >= (3, 14),
            reason="Requires EmbeddingService for local query (not available in Python 3.14)",
        )
        @pytest.mark.asyncio
        async def test_perform_semantic_search_queries(self, moss_client, loaded_index):
            """Should perform semantic search queries."""
            for test_query in TEST_QUERIES:
                results = await moss_client.query(
                    loaded_index,
                    test_query["query"],
                    QueryOptions(top_k=3),
                )

                assert hasattr(results, "docs")
                assert isinstance(results.docs, list)
                assert len(results.docs) > 0
                assert len(results.docs) <= 3

                # Verify result structure
                for item in results.docs:
                    assert hasattr(item, "id")
                    assert hasattr(item, "text")
                    assert hasattr(item, "score")
                    assert isinstance(item.id, str)
                    assert isinstance(item.text, str)
                    assert isinstance(item.score, float)
                    assert item.score > 0
                    assert item.score <= 1

                # Verify results are sorted by relevance (descending score)
                for j in range(1, len(results.docs)):
                    assert results.docs[j - 1].score >= results.docs[j].score

        @pytest.mark.skipif(
            sys.version_info >= (3, 14),
            reason="Requires EmbeddingService for local query (not available in Python 3.14)",
        )
        @pytest.mark.asyncio
        async def test_respect_topk_parameter(self, moss_client, loaded_index):
            """Should respect topK parameter."""
            top_k = 2
            results = await moss_client.query(
                loaded_index,
                "artificial intelligence",
                QueryOptions(top_k=top_k),
            )

            assert len(results.docs) <= top_k

    class TestCustomEmbeddings:
        """Validate custom embedding ingestion and query options."""

        @pytest.mark.skipif(
            sys.version_info >= (3, 14),
            reason="EmbeddingService not available in Python 3.14",
        )
        @pytest.mark.asyncio
        async def test_ingest_and_query_with_custom_embeddings(self, moss_client):
            """Should ingest and query with custom embeddings."""
            custom_index = generate_unique_index_name("test-custom")

            try:
                embedding_service = EmbeddingService(
                    model_id="moss-minilm", normalize=True, quantized=False
                )
                await embedding_service.load_model()

                document_embeddings = await embedding_service.create_embeddings(
                    [doc["text"] for doc in TEST_DOCUMENTS]
                )

                docs_with_embeddings = [
                    DocumentInfo(
                        id=source_doc["id"],
                        text=source_doc["text"],
                        embedding=document_embeddings[index],
                    )
                    for index, source_doc in enumerate(TEST_DOCUMENTS)
                ]

                created = await moss_client.create_index(
                    custom_index, docs_with_embeddings, model_id="custom"
                )
                assert created is True

                await moss_client.load_index(custom_index)

                query_embedding = await embedding_service.create_embedding(
                    "neural networks and ai fundamentals"
                )

                options = QueryOptions(
                    embedding=query_embedding, top_k=len(TEST_DOCUMENTS)
                )

                results = await moss_client.query(
                    custom_index, "neural networks and ai fundamentals", options=options
                )

                assert len(results.docs) > 0
                assert results.docs[0].id in {doc["id"] for doc in TEST_DOCUMENTS}
                assert all(getattr(doc, "score", 0) > 0 for doc in results.docs)

            finally:
                try:
                    await moss_client.delete_index(custom_index)
                except Exception:
                    pass

    class TestErrorHandling:
        """Test error handling."""

        @pytest_asyncio.fixture
        async def index_for_error_tests(self, moss_client):
            """Create an index for error handling tests and clean up after."""
            index_name = generate_unique_index_name("test-errors")

            docs = [
                DocumentInfo(id=doc["id"], text=doc["text"]) for doc in TEST_DOCUMENTS
            ]
            await moss_client.create_index(index_name, docs, TEST_MODEL_ID)

            yield index_name

            try:
                await moss_client.delete_index(index_name)
            except Exception:
                pass

        @pytest.mark.asyncio
        async def test_handle_operations_on_nonexistent_index(self, moss_client):
            """Should handle operations on non-existent index."""
            non_existent_index = "does-not-exist"

            with pytest.raises(Exception):
                await moss_client.get_docs(non_existent_index)

            with pytest.raises(Exception):
                await moss_client.query(non_existent_index, "test query")

            with pytest.raises(Exception):
                await moss_client.add_docs(
                    non_existent_index, [DocumentInfo(id="test", text="test")]
                )

            with pytest.raises(Exception):
                await moss_client.delete_docs(non_existent_index, ["test"])

        @pytest.mark.asyncio
        async def test_handle_empty_document_arrays_gracefully(
            self, moss_client, index_for_error_tests
        ):
            """Should handle empty document arrays gracefully."""
            result = await moss_client.add_docs(index_for_error_tests, [])
            assert result["added"] == 0
            assert result.get("updated", 0) == 0

        @pytest.mark.asyncio
        async def test_handle_empty_docids_array_for_deletion(
            self, moss_client, index_for_error_tests
        ):
            """Should handle empty docIds array for deletion."""
            result = await moss_client.delete_docs(index_for_error_tests, [])
            assert result["deleted"] == 0
