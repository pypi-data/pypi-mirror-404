"""Unit tests for Control Plane execution layer."""

from __future__ import annotations

import pytest

from sagellm_control import (
    ClientConfig,
    ControlPlaneManager,
    EngineClient,
    RequestContext,
    RetryPolicy,
)
from sagellm_protocol import Request


@pytest.fixture
def sample_request() -> Request:
    """Create a sample Protocol Request."""
    return Request(
        request_id="req-001",
        trace_id="trace-001",
        model="test-model",
        prompt="Hello, how are you?",
        max_tokens=100,
        stream=False,
    )


@pytest.fixture
def stream_request() -> Request:
    """Create a sample streaming Protocol Request."""
    return Request(
        request_id="req-002",
        trace_id="trace-002",
        model="test-model",
        prompt="Tell me a story",
        max_tokens=200,
        stream=True,
    )


class TestEngineClient:
    """Tests for EngineClient."""

    def test_client_config_defaults(self):
        """Should have sensible defaults."""
        config = ClientConfig()
        assert config.timeout_s == 60.0
        assert config.max_retries == 3
        assert config.retry_policy == RetryPolicy.EXPONENTIAL_BACKOFF

    def test_request_context(self):
        """Should create request context."""
        ctx = RequestContext(request_id="req-1", trace_id="trace-1")
        assert ctx.request_id == "req-1"
        assert ctx.trace_id == "trace-1"
        assert ctx.attempts == 0
        assert ctx.engines_tried == []


class TestControlPlaneManagerExecution:
    """Tests for ControlPlaneManager execute methods.

    Note: These tests verify error handling when no engines are available.
    """

    def test_manager_has_execute_methods(self):
        """Manager should have execute_request and stream_request methods."""
        manager = ControlPlaneManager()
        assert hasattr(manager, "execute_request")
        assert hasattr(manager, "stream_request")
        assert callable(manager.execute_request)
        assert callable(manager.stream_request)

    @pytest.mark.asyncio
    async def test_execute_request_no_engines(self):
        """Should return error response when no engines registered."""
        manager = ControlPlaneManager()
        request = Request(
            request_id="req-005",
            trace_id="trace-005",
            model="any-model",
            prompt="Hello",
            max_tokens=50,
            stream=False,
        )

        response = await manager.execute_request(request)

        assert response.finish_reason == "error"
        assert response.error is not None
        assert (
            "No healthy engines" in response.error.message or "No engines" in response.error.message
        )

    @pytest.mark.asyncio
    async def test_stream_request_no_engines(self):
        """Should yield error event when no engines registered."""
        manager = ControlPlaneManager()
        request = Request(
            request_id="req-006",
            trace_id="trace-006",
            model="any-model",
            prompt="Hello",
            max_tokens=50,
            stream=True,
        )

        events = []
        async for event in manager.stream_request(request):
            events.append(event)

        assert len(events) == 1
        assert events[0].event == "end"
        assert events[0].finish_reason == "error"


class TestRetryPolicy:
    """Tests for retry policy calculation."""

    def test_exponential_backoff(self):
        """Should calculate exponential backoff delays."""
        client = EngineClient(
            ClientConfig(
                retry_policy=RetryPolicy.EXPONENTIAL_BACKOFF,
                base_retry_delay_s=0.5,
                max_retry_delay_s=10.0,
            )
        )

        assert client._calculate_retry_delay(0) == 0.5
        assert client._calculate_retry_delay(1) == 1.0
        assert client._calculate_retry_delay(2) == 2.0
        assert client._calculate_retry_delay(3) == 4.0
        assert client._calculate_retry_delay(10) == 10.0  # Capped

    def test_linear_backoff(self):
        """Should calculate linear backoff delays."""
        client = EngineClient(
            ClientConfig(
                retry_policy=RetryPolicy.LINEAR_BACKOFF,
                base_retry_delay_s=1.0,
                max_retry_delay_s=5.0,
            )
        )

        assert client._calculate_retry_delay(0) == 1.0
        assert client._calculate_retry_delay(1) == 2.0
        assert client._calculate_retry_delay(2) == 3.0
        assert client._calculate_retry_delay(10) == 5.0  # Capped

    def test_no_retry(self):
        """Should return 0 delay with no retry policy."""
        client = EngineClient(ClientConfig(retry_policy=RetryPolicy.NONE))
        assert client._calculate_retry_delay(0) == 0
        assert client._calculate_retry_delay(5) == 0
