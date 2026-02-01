"""Extended integration tests for Control Plane with CPUEngine.

These tests cover:
- LocalEngineClient with CPUEngine
- Control Plane routing with local engines
- Concurrent request handling
- Error scenarios and recovery
- Metrics collection through the control plane

Requirements:
    pip install torch transformers pytest-asyncio

Note: Tests marked @pytest.mark.slow require actual model inference.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
import pytest_asyncio

from sagellm_protocol import Request

# Check if CPUEngine dependencies are available
try:
    from sagellm_backend.engine.cpu import CPUEngine, CPUEngineConfig

    CPU_ENGINE_AVAILABLE = CPUEngine.is_available()
except ImportError:
    CPU_ENGINE_AVAILABLE = False


def make_request(
    prompt: str = "Hello!",
    max_tokens: int = 10,
    stream: bool = False,
    model: str = "gpt2",
) -> Request:
    """Helper to create a test Request."""
    return Request(
        request_id=f"req-{uuid.uuid4().hex[:8]}",
        trace_id=f"trace-{uuid.uuid4().hex[:8]}",
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        stream=stream,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test: LocalEngineClient with CPUEngine
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestLocalEngineClientWithCPU:
    """Integration tests for LocalEngineClient with real CPUEngine."""

    @pytest_asyncio.fixture
    async def cpu_engine(self):
        """Create and start a CPUEngine."""
        config = CPUEngineConfig(
            engine_id=f"cpu-local-{uuid.uuid4().hex[:8]}",
            model_path="gpt2",  # Small model for fast tests
            max_new_tokens=20,
        )
        engine = CPUEngine(config)
        await engine.start()
        yield engine
        await engine.stop()

    @pytest_asyncio.fixture
    async def local_client(self, cpu_engine):
        """Create LocalEngineClient wrapping CPUEngine."""
        from sagellm_control import LocalEngineClient

        client = LocalEngineClient(cpu_engine)
        yield client
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_execute_request_through_client(self, local_client):
        """Test executing request through LocalEngineClient."""
        request = make_request(prompt="What is Python?", max_tokens=10)

        response = await local_client.execute_request(request)

        assert response.request_id == request.request_id
        assert response.trace_id == request.trace_id
        assert response.output_text is not None
        assert len(response.output_text) > 0
        assert response.metrics.ttft_ms > 0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_stream_request_through_client(self, local_client):
        """Test streaming through LocalEngineClient."""
        request = make_request(prompt="Count to 3:", max_tokens=10, stream=True)

        events = []
        async for event in local_client.stream_request(request):
            events.append(event)

        # Verify event structure (dict format)
        assert len(events) >= 2
        assert events[0]["event"] == "start"
        assert events[-1]["event"] == "end"
        assert events[-1]["metrics"]["ttft_ms"] > 0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_health_check_through_client(self, local_client):
        """Test health check through LocalEngineClient."""
        is_healthy = await local_client.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_engine_id_property(self, local_client, cpu_engine):
        """Test engine_id property access."""
        assert local_client.engine_id == cpu_engine.engine_id

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_multiple_sequential_requests(self, local_client):
        """Test multiple sequential requests through client."""
        responses = []
        for i in range(3):
            request = make_request(prompt=f"Request {i}", max_tokens=5)
            response = await local_client.execute_request(request)
            responses.append(response)

        assert len(responses) == 3
        for resp in responses:
            assert resp.output_text is not None
            assert resp.metrics.ttft_ms > 0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_requests_through_client(self, local_client):
        """Test concurrent requests through LocalEngineClient."""
        requests = [make_request(prompt=f"Concurrent {i}", max_tokens=5) for i in range(2)]

        tasks = [local_client.execute_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 2
        for resp in responses:
            assert resp.output_text is not None


# ─────────────────────────────────────────────────────────────────────────────
# Test: Control Plane Manager with Local CPU Engine
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestControlPlaneWithLocalCPU:
    """Integration tests for ControlPlaneManager with local CPUEngine."""

    @pytest_asyncio.fixture
    async def cpu_engine(self):
        """Create and start a CPUEngine."""
        config = CPUEngineConfig(
            engine_id="cpu-cp-test",
            model_path="gpt2",
            max_new_tokens=15,
        )
        engine = CPUEngine(config)
        await engine.start()
        yield engine
        await engine.stop()

    @pytest_asyncio.fixture
    async def control_plane_with_engine(self, cpu_engine):
        """Create ControlPlaneManager with registered CPUEngine."""
        from sagellm_control import ControlPlaneManager

        cp = ControlPlaneManager()

        # Register engine with metadata containing the instance
        cp.register_engine(
            engine_id=cpu_engine.engine_id,
            model_id="gpt2",
            host="local",
            port=0,
            metadata={"engine_instance": cpu_engine},
        )

        yield cp, cpu_engine

    @pytest.mark.asyncio
    async def test_engine_registration(self, control_plane_with_engine):
        """Test that CPUEngine is properly registered."""
        cp, engine = control_plane_with_engine

        engine_info = cp.get_engine(engine.engine_id)
        assert engine_info is not None
        assert engine_info.engine_id == engine.engine_id
        assert engine_info.model_id == "gpt2"

    @pytest.mark.asyncio
    async def test_route_to_registered_engine(self, control_plane_with_engine):
        """Test routing finds the registered CPUEngine."""
        cp, engine = control_plane_with_engine

        engines = cp.get_engines_for_model("gpt2")
        assert len(engines) > 0
        assert any(e.engine_id == engine.engine_id for e in engines)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_direct_engine_execution_after_routing(self, control_plane_with_engine):
        """Test executing on CPUEngine after routing."""
        cp, engine = control_plane_with_engine

        # Route to find engine
        target = cp.route_request(model_id="gpt2")
        assert target is not None

        # Execute directly on engine
        request = make_request(model="gpt2", max_tokens=5)
        response = await engine.execute(request)

        assert response.output_text is not None
        assert response.metrics.ttft_ms > 0

    @pytest.mark.asyncio
    async def test_list_engines_includes_cpu(self, control_plane_with_engine):
        """Test that list_engines includes the CPUEngine."""
        cp, engine = control_plane_with_engine

        engines = cp.list_engines()
        engine_ids = [e.engine_id for e in engines]
        assert engine.engine_id in engine_ids

    @pytest.mark.asyncio
    async def test_unregister_cpu_engine(self, control_plane_with_engine):
        """Test unregistering CPUEngine from control plane."""
        cp, engine = control_plane_with_engine

        # Should be registered
        assert cp.get_engine(engine.engine_id) is not None

        # Unregister
        cp.unregister_engine(engine.engine_id)

        # Should be gone
        assert cp.get_engine(engine.engine_id) is None


# ─────────────────────────────────────────────────────────────────────────────
# Test: Multiple CPU Engines
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestMultiCPUEngineEnvironment:
    """Test Control Plane with multiple CPU engines."""

    @pytest_asyncio.fixture
    async def mixed_environment(self):
        """Create environment with multiple CPU engines."""
        from sagellm_control import ControlPlaneManager

        # Create CPU engine
        config = CPUEngineConfig(
            engine_id="cpu-mixed-001",
            model_path="gpt2",
            max_new_tokens=10,
        )
        cpu_engine = CPUEngine(config)
        await cpu_engine.start()

        # Create second CPU engine
        config2 = CPUEngineConfig(
            engine_id="cpu-mixed-002",
            model_path="gpt2",
            max_new_tokens=10,
        )
        cpu_engine_2 = CPUEngine(config2)
        await cpu_engine_2.start()

        # Create control plane
        cp = ControlPlaneManager()

        # Register CPU engine
        cp.register_engine(
            engine_id="cpu-mixed-001",
            model_id="gpt2",
            host="local",
            port=0,
            metadata={"engine_instance": cpu_engine, "type": "cpu"},
        )

        # Register second CPU engine
        cp.register_engine(
            engine_id="cpu-mixed-002",
            model_id="gpt2",
            host="local",
            port=0,
            metadata={"engine_instance": cpu_engine_2, "type": "cpu"},
        )

        yield cp, cpu_engine, cpu_engine_2

        await cpu_engine.stop()
        await cpu_engine_2.stop()

    @pytest.mark.asyncio
    async def test_both_engines_registered(self, mixed_environment):
        """Both engines should be registered."""
        cp, _, _ = mixed_environment

        engines = cp.list_engines()
        engine_ids = [e.engine_id for e in engines]

        assert "cpu-mixed-001" in engine_ids
        assert "cpu-mixed-002" in engine_ids

    @pytest.mark.asyncio
    async def test_route_to_specific_model(self, mixed_environment):
        """Routing should find correct engine by model."""
        cp, _, _ = mixed_environment

        # Get engines for gpt2 should find CPU engines
        gpt2_engines = cp.get_engines_for_model("gpt2")
        assert len(gpt2_engines) >= 2
        assert any(e.engine_id == "cpu-mixed-001" for e in gpt2_engines)
        assert any(e.engine_id == "cpu-mixed-002" for e in gpt2_engines)


# ─────────────────────────────────────────────────────────────────────────────
# Test: Error Handling in Control Plane
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestControlPlaneErrorHandling:
    """Test error handling scenarios with CPUEngine."""

    @pytest.mark.asyncio
    async def test_route_nonexistent_model(self):
        """Routing to nonexistent model should return empty list."""
        from sagellm_control import ControlPlaneManager

        cp = ControlPlaneManager()
        engines = cp.get_engines_for_model("nonexistent-model")
        assert engines == []

    @pytest.mark.asyncio
    async def test_execute_on_stopped_engine_through_client(self):
        """Executing on stopped engine should raise error."""
        from sagellm_control import LocalEngineClient

        config = CPUEngineConfig(
            engine_id="stopped-engine",
            model_path="gpt2",
        )
        engine = CPUEngine(config)
        # Don't start the engine

        client = LocalEngineClient(engine)
        request = make_request()

        with pytest.raises(RuntimeError, match="not running"):
            await client.execute_request(request)


# ─────────────────────────────────────────────────────────────────────────────
# Test: Stress Testing
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestCPUEngineStress:
    """Stress tests for CPUEngine through Control Plane."""

    @pytest_asyncio.fixture
    async def stress_engine(self):
        """Create CPUEngine for stress testing."""
        config = CPUEngineConfig(
            engine_id="cpu-stress",
            model_path="gpt2",
            max_new_tokens=5,  # Very short for speed
        )
        engine = CPUEngine(config)
        await engine.start()
        yield engine
        await engine.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rapid_sequential_requests(self, stress_engine):
        """Test rapid sequential request execution."""
        from sagellm_control import LocalEngineClient

        client = LocalEngineClient(stress_engine)

        for i in range(5):
            request = make_request(prompt=f"Quick {i}", max_tokens=3)
            response = await client.execute_request(request)
            assert response.output_text is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_stress(self, stress_engine):
        """Test concurrent request stress."""
        from sagellm_control import LocalEngineClient

        client = LocalEngineClient(stress_engine)

        # Create 4 concurrent requests
        requests = [make_request(prompt=f"Stress {i}", max_tokens=3) for i in range(4)]

        tasks = [client.execute_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete (either success or timeout)
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.output_text)
        assert success_count >= 1  # At least one should succeed


# ─────────────────────────────────────────────────────────────────────────────
# Test: Metrics Validation Through Control Plane
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestMetricsThroughControlPlane:
    """Validate metrics collected through Control Plane."""

    @pytest_asyncio.fixture
    async def client_with_engine(self):
        """Create LocalEngineClient with CPUEngine."""
        from sagellm_control import LocalEngineClient

        config = CPUEngineConfig(
            engine_id="cpu-metrics",
            model_path="gpt2",
            max_new_tokens=10,
        )
        engine = CPUEngine(config)
        await engine.start()

        client = LocalEngineClient(engine)

        yield client, engine

        await engine.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_execute_metrics_complete(self, client_with_engine):
        """Verify execute response has complete metrics."""
        client, _ = client_with_engine

        request = make_request(max_tokens=5)
        response = await client.execute_request(request)

        metrics = response.metrics

        # Core metrics should be present
        assert metrics.ttft_ms > 0
        assert metrics.throughput_tps >= 0
        assert metrics.error_rate == 0.0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_stream_end_event_has_metrics(self, client_with_engine):
        """Verify stream end event has metrics."""
        client, _ = client_with_engine

        request = make_request(max_tokens=5, stream=True)

        end_event = None
        async for event in client.stream_request(request):
            if event["event"] == "end":
                end_event = event
                break

        assert end_event is not None
        assert "metrics" in end_event
        assert end_event["metrics"]["ttft_ms"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
