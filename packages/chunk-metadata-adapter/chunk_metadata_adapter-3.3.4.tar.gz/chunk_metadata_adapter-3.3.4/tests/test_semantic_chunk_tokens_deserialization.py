"""
Regression tests for token preservation during SemanticChunk deserialization.

These tests verify that `SemanticChunk.from_dict_with_autofill_and_validation()`
preserves `tokens` and `bm25_tokens` when a server returns them as top-level
fields (legacy response shape). The model stores these fields under `metrics`,
so the factory must remap them to avoid silent data loss.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
Created: 2025-12-21
Updated: 2025-12-21
"""

from chunk_metadata_adapter.semantic_chunk import SemanticChunk


def test_from_dict_preserves_tokens_and_bm25_tokens_in_metrics():
    """
    Ensure top-level token fields are moved into metrics during deserialization.

    Test scenario:
        - Setup: A server-like payload with top-level tokens fields
        - Action: Deserialize using from_dict_with_autofill_and_validation
        - Assertion: metrics.tokens and metrics.bm25_tokens are preserved
    """
    data = {
        "type": "Draft",
        "body": "This is a test.",
        "tokens": ["T", "h", "i", "s"],
        "bm25_tokens": ["this", "is", "test"],
    }

    chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
    assert chunk.metrics is not None
    assert chunk.metrics.tokens == ["T", "h", "i", "s"]
    assert chunk.metrics.bm25_tokens == ["this", "is", "test"]

    dumped = chunk.model_dump()
    assert "tokens" not in dumped
    assert "bm25_tokens" not in dumped
    assert dumped["metrics"]["tokens"] == ["T", "h", "i", "s"]
    assert dumped["metrics"]["bm25_tokens"] == ["this", "is", "test"]


def test_from_dict_does_not_override_existing_metrics_tokens():
    """
    Ensure that metrics-level tokens take priority over top-level fields.

    Test scenario:
        - Setup: Both top-level and metrics-level token fields present
        - Action: Deserialize
        - Assertion: Existing metrics tokens are preserved (not overridden)
    """
    data = {
        "type": "Draft",
        "body": "x",
        "tokens": ["top"],
        "bm25_tokens": ["top_bm25"],
        "metrics": {"tokens": ["metrics"], "bm25_tokens": ["metrics_bm25"]},
    }

    chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
    assert chunk.metrics is not None
    assert chunk.metrics.tokens == ["metrics"]
    assert chunk.metrics.bm25_tokens == ["metrics_bm25"]


def test_from_dict_fills_metrics_tokens_when_metrics_tokens_is_none():
    """
    Ensure that top-level tokens fill metrics fields when metrics values are None.

    Test scenario:
        - Setup: metrics contains tokens=None but top-level tokens is provided
        - Action: Deserialize
        - Assertion: metrics.tokens is filled from the top-level tokens
    """
    data = {
        "type": "Draft",
        "body": "x",
        "tokens": ["filled"],
        "metrics": {"tokens": None},
    }

    chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
    assert chunk.metrics is not None
    assert chunk.metrics.tokens == ["filled"]


def test_from_dict_accepts_metrics_tokens_as_token_objects():
    """
    Ensure metrics.tokens token objects are coerced to List[str].

    Test scenario:
        - Setup: metrics.tokens is a list of dict-like token objects
        - Action: Deserialize using from_dict_with_autofill_and_validation
        - Assertion: chunk.metrics.tokens becomes a list of token texts
    """
    data = {
        "type": "Draft",
        "body": "Test class-methods.",
        "metrics": {
            "tokens": [
                {"text": "Test", "lemma": "test", "start_char": 0, "end_char": 4},
                {
                    "text": "class",
                    "lemma": "class",
                    "start_char": 5,
                    "end_char": 10,
                },
                {"text": "-", "lemma": "-", "start_char": 10, "end_char": 11},
            ]
        },
    }

    chunk = SemanticChunk.from_dict_with_autofill_and_validation(data)
    assert chunk.metrics is not None
    assert chunk.metrics.tokens == ["Test", "class", "-"]
