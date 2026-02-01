"""
Tests for embedding_model field and 'model' alias (SVO chunker compatibility).

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
from chunk_metadata_adapter.semantic_chunk import SemanticChunk
from chunk_metadata_adapter.chunk_query import ChunkQuery
from chunk_metadata_adapter.data_types import ChunkType


class TestSemanticChunkEmbeddingModel:
    """Tests for SemanticChunk embedding_model field and model alias."""

    def test_creation_with_embedding_model(self):
        """SemanticChunk accepts embedding_model and persists it."""
        chunk = SemanticChunk(
            body="test",
            type=ChunkType.DOC_BLOCK,
            embedding=[0.1, 0.2, 0.3],
            embedding_model="text-embedding-ada-002",
        )
        assert chunk.embedding_model == "text-embedding-ada-002"

    def test_from_dict_with_embedding_model(self):
        """from_dict_with_autofill_and_validation accepts embedding_model."""
        data = {
            "body": "test",
            "type": "DocBlock",
            "embedding": [0.1, 0.2],
            "embedding_model": "text-embedding-3-small",
        }
        chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
        assert chunk.embedding_model == "text-embedding-3-small"

    def test_from_dict_model_alias_from_chunker(self):
        """from_dict maps 'model' to embedding_model (SVO chunker response)."""
        data = {
            "body": "Parse CLI arguments.",
            "type": "DocBlock",
            "embedding": [0.1] * 384,
            "model": "text-embedding-ada-002",
        }
        chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
        assert chunk.embedding_model == "text-embedding-ada-002"
        assert not hasattr(chunk, "model") or getattr(chunk, "model", None) is None

    def test_from_dict_model_alias_prefer_embedding_model(self):
        """When both 'model' and 'embedding_model' present, embedding_model wins."""
        data = {
            "body": "test",
            "type": "DocBlock",
            "embedding_model": "primary-model",
            "model": "chunker-model",
        }
        chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
        assert chunk.embedding_model == "primary-model"

    def test_from_flat_dict_embedding_model_roundtrip(self):
        """embedding_model survives flat dict round-trip."""
        chunk = SemanticChunk(
            body="test",
            type=ChunkType.DOC_BLOCK,
            embedding_model="text-embedding-ada-002",
        )
        flat = chunk.to_flat_dict(for_redis=False)
        assert flat.get("embedding_model") == "text-embedding-ada-002"
        restored = SemanticChunk.from_flat_dict(flat)
        assert restored.embedding_model == "text-embedding-ada-002"

    def test_from_flat_dict_model_alias(self):
        """from_flat_dict maps flat key 'model' to embedding_model (chunker payload)."""
        flat = {
            "body": "test",
            "type": "DocBlock",
            "embedding": "[0.1,0.2,0.3]",
            "model": "svo-embedding-model",
        }
        chunk = SemanticChunk.from_flat_dict(flat)
        assert chunk.embedding_model == "svo-embedding-model"

    def test_from_flat_dict_model_alias_prefer_embedding_model(self):
        """When flat has both model and embedding_model, embedding_model wins."""
        flat = {
            "body": "test",
            "type": "DocBlock",
            "embedding_model": "canonical",
            "model": "alias",
        }
        chunk = SemanticChunk.from_flat_dict(flat)
        assert chunk.embedding_model == "canonical"


class TestChunkQueryEmbeddingModel:
    """Tests for ChunkQuery embedding_model field and model alias."""

    def test_creation_with_embedding_model(self):
        """ChunkQuery accepts embedding_model."""
        q = ChunkQuery(type="DocBlock", embedding_model="text-embedding-ada-002")
        assert q.embedding_model == "text-embedding-ada-002"

    def test_from_flat_dict_model_alias(self):
        """ChunkQuery.from_flat_dict maps 'model' to embedding_model."""
        flat = {"type": "DocBlock", "model": "query-embedding-model"}
        q = ChunkQuery.from_flat_dict(flat)
        assert q.embedding_model == "query-embedding-model"
