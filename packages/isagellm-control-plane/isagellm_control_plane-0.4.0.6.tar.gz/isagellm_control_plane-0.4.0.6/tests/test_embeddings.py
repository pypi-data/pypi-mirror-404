"""Unit tests for embeddings functionality.

Tests get_embeddings method for ControlPlaneManager with CPU engines.
"""

from __future__ import annotations

import pytest

from sagellm_control import ControlPlaneManager


class TestControlPlaneManagerEmbeddings:
    """Tests for ControlPlaneManager get_embeddings."""

    @pytest.mark.asyncio
    async def test_get_embeddings_no_engine(self):
        """Should raise error when no embedding engines available."""
        manager = ControlPlaneManager()

        texts = ["Test text 1", "Test text 2"]

        # Should raise ValueError when no engines available
        with pytest.raises(ValueError, match="No embedding engines available"):
            await manager.get_embeddings(texts)

    @pytest.mark.asyncio
    async def test_get_embeddings_empty_texts(self):
        """Should return empty list for empty input."""
        manager = ControlPlaneManager()

        embeddings = await manager.get_embeddings([])

        assert embeddings == []

    @pytest.mark.asyncio
    async def test_get_embeddings_with_trace_id(self):
        """Should accept optional trace_id parameter but fail with no engine."""
        manager = ControlPlaneManager()

        # Should raise ValueError when no engines available, even with trace_id
        with pytest.raises(ValueError, match="No embedding engines available"):
            await manager.get_embeddings(
                texts=["Test"],
                model_id="test-model",
                trace_id="custom-trace-123",
            )


class TestEmbeddingsPredictability:
    """Tests to ensure CPU engine embeddings are predictable and consistent."""

    @pytest.mark.asyncio
    async def test_cpu_embeddings_placeholder(self):
        """Placeholder for future CPU engine embeddings tests."""
        # TODO: Once CPUEngine supports embeddings, test:
        # - Deterministic embeddings for same input
        # - Different embeddings for different texts
        # - Vector structure and dimensions
        manager = ControlPlaneManager()
        assert manager is not None  # Placeholder
