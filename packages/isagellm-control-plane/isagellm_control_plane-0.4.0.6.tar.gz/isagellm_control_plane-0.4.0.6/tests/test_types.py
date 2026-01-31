"""Unit tests for Control Plane types."""

from __future__ import annotations

import pytest

from sagellm_control.types import (
    EngineInfo,
    EngineState,
    ExecutionInstance,
    ExecutionInstanceType,
    RequestMetadata,
    RequestPriority,
    RequestStatus,
    RequestType,
    SchedulingDecision,
)


class TestEngineState:
    """Tests for EngineState enum."""

    def test_engine_states_exist(self):
        """All expected states should exist."""
        assert EngineState.STARTING.value == "STARTING"
        assert EngineState.READY.value == "READY"
        assert EngineState.DRAINING.value == "DRAINING"
        assert EngineState.STOPPED.value == "STOPPED"
        assert EngineState.ERROR.value == "ERROR"


class TestEngineInfo:
    """Tests for EngineInfo dataclass."""

    def test_create_engine_info(self):
        """Should create EngineInfo with required fields."""
        info = EngineInfo(
            engine_id="engine-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8000,
        )
        assert info.engine_id == "engine-001"
        assert info.model_id == "Qwen/Qwen2-7B"
        assert info.host == "localhost"
        assert info.port == 8000
        assert info.state == EngineState.STARTING

    def test_engine_info_health_properties(self):
        """Should correctly compute health properties."""
        info = EngineInfo(
            engine_id="engine-001",
            model_id="test-model",
            host="localhost",
            port=8000,
            state=EngineState.READY,
        )
        assert info.is_healthy is True
        assert info.is_accepting_requests is True
        assert info.is_terminal is False

        info.state = EngineState.STOPPED
        assert info.is_healthy is False
        assert info.is_terminal is True

    def test_engine_info_to_dict(self):
        """Should serialize to dictionary."""
        info = EngineInfo(
            engine_id="engine-001",
            model_id="test-model",
            host="localhost",
            port=8000,
        )
        d = info.to_dict()
        assert d["engine_id"] == "engine-001"
        assert d["model_id"] == "test-model"
        assert d["state"] == "STARTING"


class TestRequestMetadata:
    """Tests for RequestMetadata dataclass."""

    def test_create_llm_request(self):
        """Should create LLM request metadata."""
        meta = RequestMetadata(
            request_id="req-001",
            prompt="Hello, world!",
            max_tokens=128,
            request_type=RequestType.LLM_CHAT,
        )
        assert meta.request_id == "req-001"
        assert meta.is_llm_request is True
        assert meta.is_embedding_request is False

    def test_create_embedding_request(self):
        """Should create embedding request metadata."""
        meta = RequestMetadata(
            request_id="req-002",
            request_type=RequestType.EMBEDDING,
            embedding_texts=["text1", "text2"],
        )
        assert meta.is_embedding_request is True
        assert meta.is_llm_request is False
        assert meta.embedding_texts == ["text1", "text2"]

    def test_request_priority_default(self):
        """Default priority should be NORMAL."""
        meta = RequestMetadata(request_id="req-003")
        assert meta.priority == RequestPriority.NORMAL


class TestExecutionInstance:
    """Tests for ExecutionInstance dataclass."""

    def test_create_instance(self):
        """Should create execution instance."""
        instance = ExecutionInstance(
            instance_id="inst-001",
            host="localhost",
            port=8000,
            model_name="test-model",
        )
        assert instance.instance_id == "inst-001"
        assert instance.can_accept_request is True

    def test_instance_request_type_support(self):
        """Should correctly report supported request types."""
        # LLM instance
        llm_instance = ExecutionInstance(
            instance_id="llm-001",
            host="localhost",
            port=8000,
            model_name="Qwen/Qwen2-7B",
            instance_type=ExecutionInstanceType.GENERAL,
        )
        assert llm_instance.can_handle_request_type(RequestType.LLM_CHAT) is True
        assert llm_instance.can_handle_request_type(RequestType.EMBEDDING) is False

        # Embedding instance
        embed_instance = ExecutionInstance(
            instance_id="embed-001",
            host="localhost",
            port=8090,
            model_name="BAAI/bge-m3",
            instance_type=ExecutionInstanceType.EMBEDDING,
        )
        assert embed_instance.can_handle_request_type(RequestType.EMBEDDING) is True
        assert embed_instance.can_handle_request_type(RequestType.LLM_CHAT) is False

        # Mixed instance
        mixed_instance = ExecutionInstance(
            instance_id="mixed-001",
            host="localhost",
            port=8000,
            model_name="Qwen/Qwen2-7B",
            instance_type=ExecutionInstanceType.LLM_EMBEDDING,
        )
        assert mixed_instance.can_handle_request_type(RequestType.LLM_CHAT) is True
        assert mixed_instance.can_handle_request_type(RequestType.EMBEDDING) is True

    def test_instance_capacity(self):
        """Should correctly compute available capacity."""
        instance = ExecutionInstance(
            instance_id="inst-001",
            host="localhost",
            port=8000,
            model_name="test-model",
            current_load=0.3,
        )
        assert instance.available_capacity == pytest.approx(0.7, rel=0.01)


class TestSchedulingDecision:
    """Tests for SchedulingDecision dataclass."""

    def test_create_decision(self):
        """Should create scheduling decision."""
        decision = SchedulingDecision(
            request_id="req-001",
            engine_id="inst-001",
            status=RequestStatus.SCHEDULED,
        )
        assert decision.request_id == "req-001"
        assert decision.engine_id == "inst-001"
        assert decision.is_scheduled is True
