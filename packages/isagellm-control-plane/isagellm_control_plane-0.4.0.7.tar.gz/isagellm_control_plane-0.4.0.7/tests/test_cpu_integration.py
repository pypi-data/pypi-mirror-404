"""Integration tests with real CPUEngine.

These tests verify full integration between Control Plane and CPUEngine
using direct local invocation (no HTTP overhead).

Requirements:
    pip install torch transformers

Note: These tests will download models on first run.
      Use TinyLlama for fast testing.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from sagellm_protocol import Request

# Check if CPUEngine dependencies are available
try:
    from sagellm_backend.engine.cpu import CPUEngine, CPUEngineConfig

    CPU_ENGINE_AVAILABLE = CPUEngine.is_available()
except ImportError:
    CPU_ENGINE_AVAILABLE = False


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestCPUEngineIntegration:
    """Integration tests with real CPUEngine."""

    @pytest_asyncio.fixture
    async def cpu_engine(self):
        """Create and start a CPUEngine with TinyLlama model."""
        config = CPUEngineConfig(
            engine_id="cpu-test-001",
            model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # Small model for testing
            device="cpu",
            max_new_tokens=50,  # Limit tokens for fast tests
        )

        engine = CPUEngine(config)
        await engine.start()

        yield engine

        # Cleanup
        await engine.stop()

    @pytest.mark.asyncio
    async def test_cpu_engine_direct_execute(self, cpu_engine):
        """Test direct execution on CPUEngine."""
        request = Request(
            request_id="cpu-req-001",
            trace_id="cpu-trace-001",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            prompt="Hello, how are you?",
            max_tokens=20,
            stream=False,
        )

        response = await cpu_engine.execute(request)

        # Verify response structure
        assert response.request_id == request.request_id
        assert response.trace_id == request.trace_id
        assert response.output_text != ""
        assert len(response.output_tokens) > 0
        assert response.finish_reason in ["stop", "length"]

        # Verify metrics
        assert response.metrics is not None
        assert response.metrics.ttft_ms > 0  # Should have real TTFT
        assert response.metrics.throughput_tps > 0

        print(f"\n✓ CPUEngine Response: {response.output_text[:100]}...")
        print(
            f"✓ Metrics: TTFT={response.metrics.ttft_ms:.2f}ms, "
            f"Throughput={response.metrics.throughput_tps:.2f}tps"
        )

    @pytest.mark.asyncio
    async def test_cpu_engine_stream(self, cpu_engine):
        """Test streaming inference on CPUEngine."""
        request = Request(
            request_id="cpu-req-002",
            trace_id="cpu-trace-002",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            prompt="Tell me a short story",
            max_tokens=30,
            stream=True,
        )

        events = []
        async for event in cpu_engine.stream(request):
            events.append(event)

        # Verify streaming events
        assert len(events) >= 3  # start + deltas + end

        # Check start event
        start_event = events[0]
        assert start_event.event == "start"
        assert start_event.request_id == request.request_id

        # Check end event
        end_event = events[-1]
        assert end_event.event == "end"
        assert end_event.finish_reason in ["stop", "length"]
        assert end_event.metrics is not None

        # Check delta events
        deltas = [e for e in events if e.event == "delta"]
        assert len(deltas) > 0

        print(f"\n✓ CPUEngine streamed {len(deltas)} tokens")

    @pytest.mark.asyncio
    async def test_local_engine_client_with_cpu(self, cpu_engine):
        """Test LocalEngineClient with CPUEngine."""
        from sagellm_control.local_engine_client import LocalEngineClient

        client = LocalEngineClient(cpu_engine)

        request = Request(
            request_id="local-req-001",
            trace_id="local-trace-001",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            prompt="What is 2+2?",
            max_tokens=10,
            stream=False,
        )

        # Execute through client
        response = await client.execute_request(request)

        assert response.request_id == request.request_id
        assert response.output_text != ""
        assert response.metrics.ttft_ms > 0

        # Health check
        is_healthy = await client.health_check()
        assert is_healthy is True

        print(f"\n✓ LocalEngineClient Response: {response.output_text[:100]}...")

    @pytest.mark.asyncio
    async def test_local_engine_client_stream(self, cpu_engine):
        """Test LocalEngineClient streaming with CPUEngine."""
        from sagellm_control.local_engine_client import LocalEngineClient

        client = LocalEngineClient(cpu_engine)

        request = Request(
            request_id="local-req-002",
            trace_id="local-trace-002",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            prompt="Count to 5",
            max_tokens=15,
            stream=True,
        )

        # Stream through client
        events = []
        async for event_dict in client.stream_request(request):
            events.append(event_dict)

        # Verify event structure
        assert len(events) >= 3
        assert events[0]["event"] == "start"
        assert events[-1]["event"] == "end"
        assert events[-1]["metrics"]["ttft_ms"] > 0

        print(f"\n✓ LocalEngineClient streamed {len(events)} events")


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestControlPlaneWithLocalCPUEngine:
    """Integration tests for ControlPlane with local CPUEngine."""

    @pytest_asyncio.fixture
    async def control_plane_with_cpu(self):
        """Create Control Plane with registered CPUEngine."""
        from sagellm_control import ControlPlaneManager

        # Create CPUEngine
        config = CPUEngineConfig(
            engine_id="cpu-cp-001",
            model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            device="cpu",
            max_new_tokens=30,
        )
        engine = CPUEngine(config)
        await engine.start()

        # Create Control Plane
        cp = ControlPlaneManager()

        # Register engine (using special local:// protocol)
        cp.register_engine(
            engine_id="cpu-cp-001",
            model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            host="local",  # Special marker for local engines
            port=0,
            metadata={"engine_instance": engine},  # Store engine instance
        )

        yield cp, engine

        # Cleanup
        await engine.stop()

    @pytest.mark.asyncio
    async def test_control_plane_with_local_cpu_engine(self, control_plane_with_cpu):
        """Test Control Plane routing to local CPUEngine.

        Note: This is a structural test. Full integration would require
        modifying ControlPlaneManager to support local engines.
        """
        cp, engine = control_plane_with_cpu

        # Verify engine is registered
        engine_info = cp.get_engine("cpu-cp-001")
        assert engine_info is not None
        assert engine_info.engine_id == "cpu-cp-001"

        # Verify we can execute on the engine directly
        request = Request(
            request_id="cp-cpu-001",
            trace_id="cp-cpu-trace-001",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            prompt="Hello!",
            max_tokens=10,
            stream=False,
        )

        response = await engine.execute(request)
        assert response.output_text != ""

        print("\n✓ Control Plane registered CPUEngine")
        print(f"✓ Direct execution successful: {response.output_text[:50]}...")


@pytest.mark.skipif(not CPU_ENGINE_AVAILABLE, reason="CPUEngine dependencies not available")
class TestCPUEnginePerformance:
    """CPU engine performance and throughput tests."""

    @pytest_asyncio.fixture
    async def cpu_engine(self):
        """Create CPU engine for performance tests."""
        config = CPUEngineConfig(
            engine_id="cpu-perf-001",
            model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            max_new_tokens=20,
        )
        engine = CPUEngine(config)
        await engine.start()

        yield engine

        await engine.stop()

    @pytest.mark.asyncio
    async def test_cpu_performance_metrics(self, cpu_engine):
        """Test CPU engine performance metrics collection."""
        import time

        request = Request(
            request_id="perf-001",
            trace_id="perf-trace-001",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            prompt="Quick test",
            max_tokens=10,
            stream=False,
        )

        # CPU execution
        start = time.time()
        response = await cpu_engine.execute(request)
        elapsed_time = time.time() - start

        print("\n📊 CPU Engine Performance:")
        print(f"  Total time: {elapsed_time * 1000:.2f}ms")
        print(f"  TTFT: {response.metrics.ttft_ms:.2f}ms")
        print(f"  Throughput: {response.metrics.throughput_tps:.2f} tokens/s")
        print(f"  Peak memory: {response.metrics.peak_mem_mb:.2f} MB")

        # Verify response completed successfully
        assert response.finish_reason in ["stop", "length"]
        assert response.metrics.ttft_ms > 0
        assert response.metrics.throughput_tps > 0
