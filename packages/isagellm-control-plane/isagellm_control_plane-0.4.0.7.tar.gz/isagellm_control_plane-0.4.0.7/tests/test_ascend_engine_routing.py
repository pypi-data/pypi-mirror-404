"""测试 Control Plane 对 Ascend 引擎的路由支持。

验证目标：
- Control Plane 可以注册 Ascend 引擎
- 可以正确路由请求到 Ascend 引擎
- engine_kind 支持 'ascend' 标识
"""

from __future__ import annotations

from sagellm_control import ControlPlaneManager
from sagellm_control.types import EngineState


class TestAscendEngineRouting:
    """测试 Ascend 引擎路由功能。"""

    def test_register_ascend_engine(self) -> None:
        """测试注册 Ascend 引擎。"""
        manager = ControlPlaneManager()

        # 注册 Ascend 引擎
        engine_info = manager.register_engine(
            engine_id="ascend-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8001,
            engine_kind="ascend",  # 明确标识为 Ascend 引擎
            metadata={"backend_type": "ascend", "device": "npu:0"},
        )

        # 验证注册信息
        assert engine_info.engine_id == "ascend-001"
        assert engine_info.model_id == "Qwen/Qwen2-7B"
        assert engine_info.engine_kind == "ascend"
        assert engine_info.metadata["backend_type"] == "ascend"
        assert engine_info.metadata["device"] == "npu:0"
        assert engine_info.state == EngineState.STARTING

    def test_list_engines_includes_ascend(self) -> None:
        """测试列出引擎时包含 Ascend 引擎。"""
        manager = ControlPlaneManager()

        # 注册多个引擎（包括 CPU 和 Ascend）
        manager.register_engine(
            engine_id="cpu-001",
            model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            host="localhost",
            port=8000,
            engine_kind="cpu",
        )
        manager.register_engine(
            engine_id="ascend-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8001,
            engine_kind="ascend",
        )

        # 列出所有引擎
        engines = manager.list_engines()

        assert len(engines) == 2

        # 验证包含 Ascend 引擎
        ascend_engine = next((e for e in engines if e.engine_kind == "ascend"), None)
        assert ascend_engine is not None
        assert ascend_engine.engine_id == "ascend-001"

    def test_multiple_ascend_engines(self) -> None:
        """测试注册多个 Ascend 引擎（不同设备）。"""
        manager = ControlPlaneManager()

        # 注册多个 Ascend 引擎
        for i in range(4):
            manager.register_engine(
                engine_id=f"ascend-{i:03d}",
                model_id="Qwen/Qwen2-7B",
                host="localhost",
                port=8000 + i,
                engine_kind="ascend",
                metadata={"device": f"npu:{i}"},
            )

        # 验证所有引擎都已注册
        engines = manager.list_engines()
        ascend_engines = [e for e in engines if e.engine_kind == "ascend"]

        assert len(ascend_engines) == 4
        assert all(e.engine_kind == "ascend" for e in ascend_engines)

        # 验证设备分配正确
        devices = [e.metadata.get("device") for e in ascend_engines]
        assert sorted(devices) == ["npu:0", "npu:1", "npu:2", "npu:3"]

    def test_ascend_engine_kind_validation(self) -> None:
        """测试 engine_kind 的有效性（确保接受 'ascend'）。"""
        manager = ControlPlaneManager()

        # 支持的 engine_kind 值（不限于此）
        valid_kinds = ["cpu", "cuda", "ascend", "llm", "embedding"]

        for kind in valid_kinds:
            engine_id = f"{kind}-test"
            engine_info = manager.register_engine(
                engine_id=engine_id,
                model_id="test-model",
                host="localhost",
                port=8000,
                engine_kind=kind,
            )
            assert engine_info.engine_kind == kind

    def test_get_engine_by_model_with_ascend(self) -> None:
        """测试根据模型获取引擎（包括 Ascend）。"""
        manager = ControlPlaneManager()

        # 注册多个引擎加载同一模型
        manager.register_engine(
            engine_id="cpu-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8000,
            engine_kind="cpu",
        )
        manager.register_engine(
            engine_id="ascend-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8001,
            engine_kind="ascend",
        )

        # 获取该模型的所有引擎
        engines = manager.list_engines()
        qwen_engines = [e for e in engines if e.model_id == "Qwen/Qwen2-7B"]

        assert len(qwen_engines) == 2

        # 验证包含 Ascend 引擎
        engine_kinds = {e.engine_kind for e in qwen_engines}
        assert "ascend" in engine_kinds
        assert "cpu" in engine_kinds

    def test_unregister_ascend_engine(self) -> None:
        """测试注销 Ascend 引擎。"""
        manager = ControlPlaneManager()

        # 注册 Ascend 引擎
        manager.register_engine(
            engine_id="ascend-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8001,
            engine_kind="ascend",
        )

        assert manager.engine_count == 1

        # 注销引擎
        manager.unregister_engine("ascend-001")

        assert manager.engine_count == 0

    def test_ascend_engine_metadata(self) -> None:
        """测试 Ascend 引擎的元数据存储。"""
        manager = ControlPlaneManager()

        # 注册带有详细元数据的 Ascend 引擎
        metadata = {
            "backend_type": "ascend",
            "device": "npu:0",
            "npu_version": "CANN 8.0",
            "max_batch_size": 64,
            "memory_mb": 32768,
        }

        engine_info = manager.register_engine(
            engine_id="ascend-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8001,
            engine_kind="ascend",
            metadata=metadata,
        )

        # 验证元数据完整保存
        assert engine_info.metadata == metadata
        assert engine_info.metadata["backend_type"] == "ascend"
        assert engine_info.metadata["device"] == "npu:0"
        assert engine_info.metadata["max_batch_size"] == 64
