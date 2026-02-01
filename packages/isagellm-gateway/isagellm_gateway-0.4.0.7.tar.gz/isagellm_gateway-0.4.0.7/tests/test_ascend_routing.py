"""测试 Gateway 对 Ascend 引擎的适配支持。

验证目标：
- Gateway 可以通过 Control Plane 路由到 Ascend 引擎
- Control Plane 的 engine_kind 机制支持 Ascend
- 架构层面的路由正确性验证

注意：
- 本测试专注于架构验证（engine_kind 支持）
- 使用 Control Plane 的引擎注册机制验证 Ascend 支持
- 真实端到端推理测试需要额外的集成环境
"""

from __future__ import annotations

from sagellm_control import ControlPlaneManager


class TestGatewayAscendRouting:
    """测试 Gateway 的 Ascend 引擎路由（架构验证）。"""

    def test_control_plane_supports_ascend_engine_kind(self) -> None:
        """验证 Control Plane 支持 engine_kind='ascend'。"""
        manager = ControlPlaneManager()

        # 注册 Ascend 引擎
        engine_info = manager.register_engine(
            engine_id="ascend-001",
            model_id="Qwen/Qwen2-7B",
            host="localhost",
            port=8001,
            engine_kind="ascend",  # 关键：验证 ascend 标识被接受
            metadata={"backend_type": "ascend", "device": "npu:0"},
        )

        # 验证注册成功
        assert engine_info.engine_kind == "ascend"
        assert engine_info.metadata["backend_type"] == "ascend"

    def test_list_engines_includes_ascend_type(self) -> None:
        """验证列出引擎时包含 Ascend 类型。"""
        manager = ControlPlaneManager()

        # 注册多种引擎类型
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

        # 验证两种引擎都已注册
        engines = manager.list_engines()
        engine_kinds = {e.engine_kind for e in engines}

        assert "cpu" in engine_kinds
        assert "ascend" in engine_kinds

    def test_multiple_ascend_engines_registration(self) -> None:
        """验证可以注册多个 Ascend 引擎。"""
        manager = ControlPlaneManager()

        # 注册多个 Ascend 引擎（不同设备）
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

        # 验证设备分配正确
        devices = sorted([e.metadata.get("device") for e in ascend_engines])
        assert devices == ["npu:0", "npu:1", "npu:2", "npu:3"]

    def test_ascend_engine_metadata_storage(self) -> None:
        """验证 Ascend 引擎的元数据存储。"""
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

    def test_ascend_and_cpu_engines_coexist(self) -> None:
        """验证 Ascend 和 CPU 引擎可以共存。"""
        manager = ControlPlaneManager()

        # 注册两种引擎加载同一模型
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

        # 验证两种引擎都已注册
        engines = manager.list_engines()
        qwen_engines = [e for e in engines if e.model_id == "Qwen/Qwen2-7B"]

        assert len(qwen_engines) == 2

        # 验证包含两种引擎类型
        engine_kinds = {e.engine_kind for e in qwen_engines}
        assert engine_kinds == {"cpu", "ascend"}
