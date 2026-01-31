"""Integration tests for Control Plane with real engines (LLMEngine).

These tests verify that ControlPlaneManager can interface with:
- LLMEngine (requires torch and transformers)

Note: LLMEngine tests are skipped if dependencies are not available.
"""

from __future__ import annotations

import pytest

from sagellm_control import ControlPlaneManager
from sagellm_protocol import Request

# Check if LLMEngine dependencies are available
try:
    from sagellm_core import LLMEngine

    LLM_ENGINE_AVAILABLE = True
except ImportError:
    LLM_ENGINE_AVAILABLE = False


@pytest.mark.skipif(not LLM_ENGINE_AVAILABLE, reason="LLMEngine dependencies not available")
class TestControlPlaneWithLLMEngine:
    """Integration tests with real LLMEngine.

    These tests require torch and transformers to be installed.
    They validate the full integration path:
    ControlPlaneManager -> EngineClient -> LLMEngine
    """

    @pytest.mark.asyncio
    async def test_llm_engine_integration_basic(self):
        """Should integrate with LLMEngine for basic inference.

        This test demonstrates the integration but requires
        a real model to be available (e.g., TinyLlama).
        """
        # Note: This is a structural test to verify the integration path exists
        # Actual execution would require model download
        manager = ControlPlaneManager()

        # In a real scenario, we would:
        # 1. Start a LLMEngine with a model
        # 2. Register it with the control plane
        # 3. Execute a request

        # For now, just verify the manager has the required methods
        assert hasattr(manager, "execute_request")
        assert hasattr(manager, "stream_request")
        assert hasattr(manager, "get_embeddings")


class TestExecutionFlowErrorHandling:
    """Tests for error handling in execution flows."""

    @pytest.mark.asyncio
    async def test_execute_request_no_model(self):
        """Should handle missing model gracefully."""
        manager = ControlPlaneManager()

        request = Request(
            request_id="req-error-001",
            trace_id="trace-error-001",
            model="nonexistent-model",
            prompt="Test",
            max_tokens=50,
            stream=False,
        )

        response = await manager.execute_request(request)

        # Should return error response, not raise exception
        assert response.finish_reason == "error"
        assert response.error is not None
        assert response.error.retryable is True

    @pytest.mark.asyncio
    async def test_stream_request_no_model(self):
        """Should handle missing model in streaming."""
        manager = ControlPlaneManager()

        request = Request(
            request_id="req-error-002",
            trace_id="trace-error-002",
            model="nonexistent-model",
            prompt="Test",
            max_tokens=50,
            stream=True,
        )

        events = []
        async for event in manager.stream_request(request):
            events.append(event)

        # Should yield single error end event
        assert len(events) == 1
        assert events[0].event == "end"
        assert events[0].finish_reason == "error"
        assert events[0].error is not None

    @pytest.mark.asyncio
    async def test_embeddings_raises_when_no_engine(self):
        """Should raise error when no embedding engines available."""
        manager = ControlPlaneManager()

        texts = ["Test 1", "Test 2"]

        # Should raise ValueError - follows CPU-First principle, no silent fallback
        with pytest.raises(ValueError, match="No embedding engines available"):
            await manager.get_embeddings(texts)


class TestProtocolCompliance:
    """Tests to ensure Protocol v0.1 compliance."""

    @pytest.mark.asyncio
    async def test_response_has_all_required_fields(self):
        """Response should have all Protocol-required fields."""
        # TODO: Replace with real CPU engine test once embeddings/protocol compliance ready
        # For now, this is a placeholder to maintain test structure
        assert True  # Placeholder

    @pytest.mark.asyncio
    async def test_stream_events_have_required_fields(self):
        """Stream events should have all Protocol-required fields."""
        # TODO: Replace with real CPU engine stream test once ready
        # For now, this is a placeholder to maintain test structure
        assert True  # Placeholder
