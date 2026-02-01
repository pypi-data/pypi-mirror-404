"""Unit tests for sageLLM Control Plane."""

from __future__ import annotations

import pytest

from sagellm_control import (
    ControlPlaneManager,
    EngineInfo,
    EngineState,
)


class TestEngineInfo:
    """Tests for EngineInfo dataclass."""

    def test_create_engine_info(self) -> None:
        """Test creating EngineInfo."""
        engine = EngineInfo(
            engine_id="engine-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8000,
        )
        assert engine.engine_id == "engine-001"
        assert engine.model_id == "Qwen/Qwen2-7B"
        assert engine.state == EngineState.STARTING
        assert engine.endpoint == "http://localhost:8000"

    def test_engine_info_health_properties(self) -> None:
        """Test health-related properties."""
        engine = EngineInfo(
            engine_id="engine-001",
            model_id="test-model",
            host="localhost",
            port=8000,
            state=EngineState.READY,
        )
        assert engine.is_healthy is True
        assert engine.is_accepting_requests is True
        assert engine.is_terminal is False

        engine.state = EngineState.STOPPED
        assert engine.is_healthy is False
        assert engine.is_terminal is True

    def test_engine_info_to_dict(self) -> None:
        """Test serialization."""
        engine = EngineInfo(
            engine_id="engine-001",
            model_id="test-model",
            host="localhost",
            port=8000,
        )
        d = engine.to_dict()
        assert d["engine_id"] == "engine-001"
        assert d["model_id"] == "test-model"
        assert d["state"] == "STARTING"


class TestControlPlaneManager:
    """Tests for ControlPlaneManager."""

    def test_create_manager(self) -> None:
        """Test manager creation."""
        manager = ControlPlaneManager(
            scheduling_policy="fifo",
            routing_strategy="round_robin",
        )
        assert manager.engine_count == 0

    def test_register_and_list_engines(self) -> None:
        """Test engine registration and listing."""
        manager = ControlPlaneManager()
        manager.register_engine(
            engine_id="engine-001",
            model_id="test-model",
            host="localhost",
            port=8000,
        )
        assert manager.engine_count == 1

        engines = manager.list_engines()
        assert len(engines) == 1
        assert engines[0].engine_id == "engine-001"

    def test_update_engine_state(self) -> None:
        """Test engine state updates."""
        manager = ControlPlaneManager()
        manager.register_engine("engine-001", model_id="test-model", host="localhost", port=8000)

        result = manager.update_engine_state("engine-001", EngineState.READY)
        assert result is True

        engine = manager.get_engine("engine-001")
        assert engine is not None
        assert engine.state == EngineState.READY

    @pytest.mark.asyncio
    async def test_schedule_request(self) -> None:
        """Test request scheduling through manager."""
        manager = ControlPlaneManager()
        manager.register_engine("engine-001", model_id="test-model", host="localhost", port=8000)
        manager.update_engine_state("engine-001", EngineState.READY)

        decision = await manager.schedule_request(
            request_id="req-001",
            trace_id="trace-001",
            model_id="test-model",
        )
        assert decision.is_scheduled

    def test_get_status(self) -> None:
        """Test status summary."""
        manager = ControlPlaneManager()
        manager.register_engine("engine-001", model_id="test-model", host="localhost", port=8000)
        manager.update_engine_state("engine-001", EngineState.READY)

        status = manager.get_status()
        assert status["total_engines"] == 1
        assert status["healthy_engines"] == 1
        assert "test-model" in status["models"]
