"""Gateway + Control Plane 集成测试 (MVP).

验证：
1. Gateway 正确初始化 Control Plane
2. OpenAI API 端点可用
3. 请求正确路由到引擎
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_gateway_control_plane_integration():
    """测试 Gateway 与 Control Plane 的集成."""
    from sagellm_control import ControlPlaneManager, EngineState
    from sagellm_gateway import SageLLMAdapter

    # 1. 创建 Control Plane
    control_plane = ControlPlaneManager()

    # 2. 注册测试引擎
    control_plane.register_engine(
        engine_id="test-engine-001",
        model_id="test-model",
        host="localhost",
        port=9000,
        engine_kind="llm",
    )
    control_plane.update_engine_state("test-engine-001", EngineState.READY)

    # 3. 创建 Gateway Adapter
    adapter = SageLLMAdapter(control_plane=control_plane)
    await adapter.initialize()

    # 4. 测试 list_models
    models = await adapter.list_models()
    assert len(models) > 0, "Should have at least one model"
    assert any(m["id"] == "test-model" for m in models), "test-model should be available"

    # 5. 清理
    control_plane.unregister_engine("test-engine-001")


@pytest.mark.asyncio
async def test_pd_separation_engine_registration():
    """测试 PD 分离实例注册."""
    from sagellm_control import ControlPlaneManager, EngineState, ExecutionInstanceType

    control_plane = ControlPlaneManager()

    # 注册 Prefilling 实例
    control_plane.register_engine(
        engine_id="prefill-001",
        model_id="Qwen2-7B",
        host="localhost",
        port=8002,
        metadata={"instance_type": ExecutionInstanceType.PREFILLING.value},
    )

    # 注册 Decoding 实例
    control_plane.register_engine(
        engine_id="decode-001",
        model_id="Qwen2-7B",
        host="localhost",
        port=8003,
        metadata={"instance_type": ExecutionInstanceType.DECODING.value},
    )

    # 验证状态
    status = control_plane.get_status()
    assert "engine_types" in status, "Status should include engine_types"
    assert status["engine_types"].get("prefilling", 0) == 1
    assert status["engine_types"].get("decoding", 0) == 1

    # 清理
    control_plane.unregister_engine("prefill-001")
    control_plane.unregister_engine("decode-001")


@pytest.mark.asyncio
async def test_scaling_manager_mvp():
    """测试 Scaling Manager MVP 功能."""
    from sagellm_control import ControlPlaneManager, ScalingManager

    control_plane = ControlPlaneManager()
    scaling_manager = ScalingManager(control_plane)

    # 1. 获取扩缩容建议（应返回 TODO 占位）
    recommendations = scaling_manager.get_scaling_recommendations()
    assert "recommendation" in recommendations
    assert "TODO" in recommendations["recommendation"]

    # 2. 尝试扩容（应抛出 NotImplementedError）
    with pytest.raises(NotImplementedError) as exc_info:
        await scaling_manager.scale_up(model_id="test-model")

    assert "TODO" in str(exc_info.value)

    # 3. 注册测试引擎并尝试缩容
    control_plane.register_engine(
        engine_id="test-engine",
        model_id="test-model",
        host="localhost",
        port=9000,
    )

    stopped = await scaling_manager.scale_down(
        engine_ids=["test-engine"],
        graceful=True,
    )

    assert "test-engine" in stopped

    # 验证引擎已被标记为 DRAINING
    from sagellm_control import EngineState

    engine = control_plane.get_engine("test-engine")
    assert engine is not None
    assert engine.state == EngineState.DRAINING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
