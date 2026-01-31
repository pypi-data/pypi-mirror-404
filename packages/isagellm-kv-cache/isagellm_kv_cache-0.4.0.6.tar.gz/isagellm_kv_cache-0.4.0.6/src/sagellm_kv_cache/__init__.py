"""sagellm-kv-cache: KV Cache Management Module for sageLLM.

本模块提供 KV Cache 管理功能，包括：
- 本地模型类：KVHandle 及其相关类型
- 错误体系：KVCacheError 及其子类
- MVP: KV Transfer Engine（Task1.3）
- (TODO) Prefix Cache: Task2.1
- (TODO) KV Pool: Task2.2
- (TODO) Eviction Policy: Task2.3

使用示例：
    >>> from sagellm_kv_cache import KVHandle, KVBudgetExceededError, KVTransferEngine
    >>> handle = KVHandle.create(num_tokens=128, device="cpu")
    >>> print(handle.to_dict())
"""

from __future__ import annotations

__version__ = "0.4.0.6"

# ============================================================
# 本地模型类 (Agent 2)
# ============================================================
# ============================================================
# 错误体系 (Agent 2)
# ============================================================
# ============================================================
# 分布式池化接口（预留，未来实现）
# ============================================================
from sagellm_kv_cache.distributed import (
    GlobalKVPoolManager,  # 全局池管理器抽象接口
    NodeContribution,  # 节点内存贡献配置
    RemoteKVAccessor,  # 远程 KV 访问层接口
)
from sagellm_kv_cache.errors import (
    KVAllPinnedError,
    # 预算/资源错误
    KVBudgetExceededError,
    # 基类
    KVCacheError,
    # 缓存错误
    KVCacheMissError,
    KVChecksumMismatchError,
    KVConfigInvalidError,
    # 配置错误
    KVConfigMissingError,
    KVDoubleFreeError,
    KVEvictionFailedError,
    KVHandleNotFoundError,
    KVHandlePinnedError,
    # 句柄操作错误
    KVInvalidHandleError,
    KVMemoryExhaustedError,
    KVMetadataMismatchError,
    KVNotImplementedError,
    # 驱逐错误
    KVNoVictimError,
    KVPoolFullError,
    KVPrefixTooLongError,
    KVRefCountUnderflowError,
    # 传输错误
    KVTransferFailedError,
    KVTransferTimeoutError,
)
from sagellm_kv_cache.models import (
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

# ============================================================
# MVP: KV Transfer Engine (Task1.3)
# ============================================================
from sagellm_kv_cache.transfer import KVTransferEngine

__all__ = [
    "__version__",
    # === 本地模型类 ===
    "KVHandle",
    "KVBlock",
    "KVTransferMetadata",
    "PrefixCacheEntry",
    "EvictionCandidate",
    "SchedulerRequest",
    "SchedulerPlan",
    "LifetimePrediction",
    "KVPoolStats",
    # === MVP: KV Transfer Engine ===
    "KVTransferEngine",
    # === 分布式池化接口（预留） ===
    "GlobalKVPoolManager",
    "NodeContribution",
    "RemoteKVAccessor",
    # === 枚举类型 ===
    "KVBlockState",
    "DType",
    "Layout",
    "MemoryTier",
    "EvictionPolicy",
    # === 错误基类 ===
    "KVCacheError",
    # === 预算/资源错误 ===
    "KVBudgetExceededError",
    "KVMemoryExhaustedError",
    "KVPoolFullError",
    # === 句柄操作错误 ===
    "KVInvalidHandleError",
    "KVDoubleFreeError",
    "KVHandlePinnedError",
    "KVHandleNotFoundError",
    "KVRefCountUnderflowError",
    # === 缓存错误 ===
    "KVCacheMissError",
    "KVPrefixTooLongError",
    # === 驱逐错误 ===
    "KVNoVictimError",
    "KVEvictionFailedError",
    "KVAllPinnedError",
    # === 传输错误 ===
    "KVTransferFailedError",
    "KVTransferTimeoutError",
    "KVChecksumMismatchError",
    "KVMetadataMismatchError",
    # === 配置错误 ===
    "KVConfigMissingError",
    "KVConfigInvalidError",
    "KVNotImplementedError",
]
