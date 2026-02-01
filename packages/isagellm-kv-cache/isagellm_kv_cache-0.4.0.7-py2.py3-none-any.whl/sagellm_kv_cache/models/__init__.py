"""sagellm-kv-cache Models 模块

本模块提供 KV Cache 的本地模型类，包括：
- KVHandle：本地扩展的 KV 句柄类
- 其他 Protocol 类型的便捷重导出

使用示例：
    >>> from sagellm_kv_cache.models import KVHandle, KVBlock
    >>> handle = KVHandle.create(num_tokens=128, device="cpu")
    >>> print(handle.to_dict())
"""

from __future__ import annotations

from sagellm_kv_cache.models.kv_handle import (
    DType,
    EvictionCandidate,
    EvictionPolicy,
    KVBlock,
    KVBlockState,
    KVHandle,
    KVPoolStats,
    KVTransferMetadata,
    Layout,
    LifetimePrediction,
    MemoryTier,
    PrefixCacheEntry,
    SchedulerPlan,
    SchedulerRequest,
)

__all__ = [
    # 本地扩展类型
    "KVHandle",
    # Protocol 类型
    "KVBlock",
    "KVTransferMetadata",
    "PrefixCacheEntry",
    "EvictionCandidate",
    "SchedulerRequest",
    "SchedulerPlan",
    "LifetimePrediction",
    "KVPoolStats",
    # 枚举类型
    "KVBlockState",
    "DType",
    "Layout",
    "MemoryTier",
    "EvictionPolicy",
]
