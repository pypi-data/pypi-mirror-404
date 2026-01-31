"""测试分布式池化接口的预留功能

验证：
1. KVHandle 支持 node_rank 字段
2. KVPool 支持 node_rank 参数
3. 分布式池化接口可导入（虽未实现）
"""

from __future__ import annotations

import pytest

from sagellm_kv_cache import (
    GlobalKVPoolManager,
    KVHandle,
    NodeContribution,
    RemoteKVAccessor,
)
from sagellm_kv_cache.pool import KVPool


class TestNodeRankSupport:
    """测试 node_rank 字段支持"""

    def test_kv_handle_with_node_rank(self) -> None:
        """测试 KVHandle 支持 node_rank 参数"""
        handle = KVHandle.create(num_tokens=128, device="cpu", node_rank=2)

        assert handle.node_rank == 2
        assert handle.num_tokens == 128

    def test_kv_handle_without_node_rank(self) -> None:
        """测试 KVHandle 默认 node_rank=None（本地）"""
        handle = KVHandle.create(num_tokens=128, device="cpu")

        assert handle.node_rank is None

    def test_kv_handle_is_local(self) -> None:
        """测试 is_local() 方法"""
        handle_local = KVHandle.create(num_tokens=128, device="cpu", node_rank=None)
        handle_node_0 = KVHandle.create(num_tokens=128, device="cpu", node_rank=0)
        handle_node_1 = KVHandle.create(num_tokens=128, device="cpu", node_rank=1)

        # node_rank=None 总是本地
        assert handle_local.is_local(current_rank=0) is True
        assert handle_local.is_local(current_rank=1) is True

        # node_rank=0 只在 rank 0 本地
        assert handle_node_0.is_local(current_rank=0) is True
        assert handle_node_0.is_local(current_rank=1) is False

        # node_rank=1 只在 rank 1 本地
        assert handle_node_1.is_local(current_rank=0) is False
        assert handle_node_1.is_local(current_rank=1) is True

    def test_kv_pool_with_node_rank(self) -> None:
        """测试 KVPool 支持 node_rank 参数"""
        pool = KVPool(max_tokens=1024, node_rank=2)

        assert pool.node_rank == 2
        assert pool.max_tokens == 1024

    def test_kv_pool_without_node_rank(self) -> None:
        """测试 KVPool 默认 node_rank=None（单机模式）"""
        pool = KVPool(max_tokens=1024)

        assert pool.node_rank is None

    def test_kv_pool_alloc_sets_node_rank(self) -> None:
        """测试 KVPool.alloc() 自动设置 node_rank"""
        pool = KVPool(max_tokens=1024, node_rank=3)
        handle = pool.alloc(128, dtype="fp16", layout="contiguous", device="cpu")

        # 应该自动继承 pool 的 node_rank
        assert handle.node_rank == 3

    def test_kv_pool_alloc_without_node_rank(self) -> None:
        """测试 KVPool.alloc() 在单机模式下不设置 node_rank"""
        pool = KVPool(max_tokens=1024, node_rank=None)
        handle = pool.alloc(128, dtype="fp16", layout="contiguous", device="cpu")

        # 应该保持 None
        assert handle.node_rank is None


class TestDistributedInterfacesImportable:
    """测试分布式接口可导入（虽未实现）"""

    def test_global_kv_pool_manager_importable(self) -> None:
        """测试 GlobalKVPoolManager 可导入"""
        assert GlobalKVPoolManager is not None
        assert hasattr(GlobalKVPoolManager, "__abstractmethods__")

    def test_node_contribution_importable(self) -> None:
        """测试 NodeContribution 可导入"""
        assert NodeContribution is not None

    def test_remote_kv_accessor_importable(self) -> None:
        """测试 RemoteKVAccessor 可导入"""
        assert RemoteKVAccessor is not None
        assert hasattr(RemoteKVAccessor, "__abstractmethods__")

    def test_node_contribution_validation(self) -> None:
        """测试 NodeContribution 验证逻辑"""
        # 正常配置
        contrib = NodeContribution(
            node_rank=0,
            total_memory_gb=100.0,
            contributed_memory_gb=40.0,
            reserved_memory_gb=60.0,
            storage_tiers=["gpu", "cpu"],
        )
        assert contrib.node_rank == 0
        assert contrib.contributed_memory_gb == 40.0

        # 超额分配应失败
        with pytest.raises(ValueError, match="Contributed.*Reserved.*Total"):
            NodeContribution(
                node_rank=0,
                total_memory_gb=100.0,
                contributed_memory_gb=60.0,
                reserved_memory_gb=50.0,  # 60 + 50 > 100
                storage_tiers=["gpu"],
            )

        # 负数应失败
        with pytest.raises(ValueError, match="must be non-negative"):
            NodeContribution(
                node_rank=0,
                total_memory_gb=100.0,
                contributed_memory_gb=-10.0,
                reserved_memory_gb=60.0,
                storage_tiers=["gpu"],
            )


class TestDistributedInterfaceDocumentation:
    """测试分布式接口的文档完整性"""

    def test_global_kv_pool_manager_has_methods(self) -> None:
        """测试 GlobalKVPoolManager 定义了所需方法"""
        required_methods = [
            "__init__",
            "alloc",
            "free",
            "get",
            "get_global_stats",
            "rebalance",
        ]

        for method in required_methods:
            assert hasattr(GlobalKVPoolManager, method), f"Missing method: {method}"

    def test_remote_kv_accessor_has_methods(self) -> None:
        """测试 RemoteKVAccessor 定义了所需方法"""
        required_methods = ["fetch", "prefetch", "is_remote"]

        for method in required_methods:
            assert hasattr(RemoteKVAccessor, method), f"Missing method: {method}"
