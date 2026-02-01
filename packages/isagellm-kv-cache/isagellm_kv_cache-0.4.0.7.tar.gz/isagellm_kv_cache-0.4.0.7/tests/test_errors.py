"""Tests for sagellm_kv_cache.errors

测试 KV Cache 错误类的功能：
- 错误基类行为
- 各类错误的初始化与消息格式
- 可重试判断
- 序列化

Author: sageLLM Team (Agent 2)
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sagellm_protocol.kv import KVErrorCode

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


class TestKVCacheErrorBase:
    """测试 KVCacheError 基类"""

    def test_basic_initialization(self):
        """测试基类初始化"""
        error = KVCacheError(
            code=KVErrorCode.BUDGET_EXCEEDED,
            message="Test error message",
        )

        assert error.code == KVErrorCode.BUDGET_EXCEEDED
        assert error.message == "Test error message"
        assert error.context == {}
        assert error.cause is None

    def test_with_context(self):
        """测试带上下文的初始化"""
        ctx = {"key": "value", "count": 42}
        error = KVCacheError(
            code=KVErrorCode.INVALID_HANDLE,
            message="Error with context",
            context=ctx,
        )

        assert error.context == ctx

    def test_with_cause(self):
        """测试带原因的初始化"""
        original = ValueError("Original error")
        error = KVCacheError(
            code=KVErrorCode.TRANSFER_FAILED,
            message="Wrapped error",
            cause=original,
        )

        assert error.cause is original

    def test_to_dict(self):
        """测试 to_dict() 方法"""
        error = KVCacheError(
            code=KVErrorCode.BUDGET_EXCEEDED,
            message="Test message",
            context={"requested": 100},
        )
        data = error.to_dict()

        assert data["error_type"] == "KVCacheError"
        assert data["code"] == "KV_BUDGET_EXCEEDED"
        assert data["message"] == "Test message"
        assert data["context"] == {"requested": 100}
        assert "retryable" in data

    def test_is_retryable(self):
        """测试可重试判断"""
        # 不可重试
        error = KVCacheError(code=KVErrorCode.BUDGET_EXCEEDED, message="")
        assert not error.is_retryable()

        # 可重试（TRANSFER_TIMEOUT 是可重试的）
        error = KVCacheError(code=KVErrorCode.TRANSFER_TIMEOUT, message="")
        assert error.is_retryable()

    def test_str_repr(self):
        """测试字符串表示"""
        error = KVCacheError(
            code=KVErrorCode.INVALID_HANDLE,
            message="Handle not found",
        )

        assert "[KV_INVALID_HANDLE]" in str(error)
        assert "Handle not found" in str(error)
        assert "KVCacheError" in repr(error)


class TestBudgetErrors:
    """测试预算/资源错误"""

    def test_budget_exceeded_error(self):
        """测试 KVBudgetExceededError"""
        error = KVBudgetExceededError(requested=1000, available=500)

        assert error.code == KVErrorCode.BUDGET_EXCEEDED
        assert error.requested == 1000
        assert error.available == 500
        assert "1000" in error.message
        assert "500" in error.message
        assert "tokens" in error.message

    def test_budget_exceeded_error_with_bytes(self):
        """测试 KVBudgetExceededError 使用字节单位"""
        error = KVBudgetExceededError(requested=2048, available=1024, unit="bytes")

        assert error.unit == "bytes"
        assert "bytes" in error.message

    def test_memory_exhausted_error(self):
        """测试 KVMemoryExhaustedError"""
        error = KVMemoryExhaustedError(required_bytes=1024 * 1024, device="cuda:0")

        assert error.code == KVErrorCode.MEMORY_EXHAUSTED
        assert error.required_bytes == 1024 * 1024
        assert error.device == "cuda:0"
        assert "cuda:0" in error.message

    def test_pool_full_error(self):
        """测试 KVPoolFullError"""
        error = KVPoolFullError(total_blocks=256)

        assert error.code == KVErrorCode.POOL_FULL
        assert error.total_blocks == 256
        assert "256" in error.message


class TestHandleErrors:
    """测试句柄操作错误"""

    def test_invalid_handle_error(self):
        """测试 KVInvalidHandleError"""
        handle_id = uuid4()
        error = KVInvalidHandleError(handle_id=handle_id, reason="expired")

        assert error.code == KVErrorCode.INVALID_HANDLE
        assert str(handle_id) in error.handle_id
        assert "expired" in error.message

    def test_double_free_error(self):
        """测试 KVDoubleFreeError"""
        handle_id = "test-handle-123"
        error = KVDoubleFreeError(handle_id=handle_id)

        assert error.code == KVErrorCode.DOUBLE_FREE
        assert error.handle_id == handle_id
        assert "already been freed" in error.message

    def test_handle_pinned_error(self):
        """测试 KVHandlePinnedError"""
        error = KVHandlePinnedError(
            handle_id="h-123",
            operation="evict",
            pin_count=3,
        )

        assert error.code == KVErrorCode.HANDLE_PINNED
        assert error.operation == "evict"
        assert error.pin_count == 3
        assert "evict" in error.message
        assert "3" in error.message

    def test_handle_not_found_error(self):
        """测试 KVHandleNotFoundError"""
        error = KVHandleNotFoundError(handle_id="missing-handle")

        assert error.code == KVErrorCode.HANDLE_NOT_FOUND
        assert "missing-handle" in error.message

    def test_ref_count_underflow_error(self):
        """测试 KVRefCountUnderflowError"""
        error = KVRefCountUnderflowError(handle_id="h-456", current_count=0)

        assert error.code == KVErrorCode.REF_COUNT_UNDERFLOW
        assert error.current_count == 0
        assert "underflow" in error.message.lower()


class TestCacheErrors:
    """测试缓存错误"""

    def test_cache_miss_error(self):
        """测试 KVCacheMissError"""
        error = KVCacheMissError(prefix_hash="abc123", prefix_len=128)

        assert error.code == KVErrorCode.CACHE_MISS
        assert error.prefix_hash == "abc123"
        assert error.prefix_len == 128
        assert "abc123" in error.message

    def test_prefix_too_long_error(self):
        """测试 KVPrefixTooLongError"""
        error = KVPrefixTooLongError(prefix_len=2048, max_len=1024)

        assert error.code == KVErrorCode.PREFIX_TOO_LONG
        assert error.prefix_len == 2048
        assert error.max_len == 1024
        assert "2048" in error.message
        assert "1024" in error.message


class TestEvictionErrors:
    """测试驱逐错误"""

    def test_no_victim_error(self):
        """测试 KVNoVictimError"""
        error = KVNoVictimError(
            bytes_needed=10240,
            pinned_count=50,
            total_count=50,
        )

        assert error.code == KVErrorCode.NO_VICTIM
        assert error.bytes_needed == 10240
        assert error.pinned_count == 50
        assert "10240" in error.message
        assert "50/50" in error.message

    def test_eviction_failed_error(self):
        """测试 KVEvictionFailedError"""
        error = KVEvictionFailedError(handle_id="h-789", reason="in use by another process")

        assert error.code == KVErrorCode.EVICTION_FAILED
        assert "h-789" in error.handle_id
        assert "in use" in error.message

    def test_all_pinned_error(self):
        """测试 KVAllPinnedError"""
        error = KVAllPinnedError(candidate_count=32)

        assert error.code == KVErrorCode.ALL_PINNED
        assert error.candidate_count == 32
        assert "32" in error.message


class TestTransferErrors:
    """测试传输错误"""

    def test_transfer_failed_error(self):
        """测试 KVTransferFailedError"""
        transfer_id = uuid4()
        error = KVTransferFailedError(
            transfer_id=transfer_id,
            source="cuda:0",
            target="cuda:1",
            reason="NCCL connection failed",
        )

        assert error.code == KVErrorCode.TRANSFER_FAILED
        assert str(transfer_id) in error.transfer_id
        assert error.source == "cuda:0"
        assert error.target == "cuda:1"
        assert "NCCL" in error.message

    def test_transfer_timeout_error(self):
        """测试 KVTransferTimeoutError"""
        error = KVTransferTimeoutError(
            transfer_id="t-123",
            timeout_seconds=30.0,
            elapsed_seconds=45.5,
        )

        assert error.code == KVErrorCode.TRANSFER_TIMEOUT
        assert error.timeout_seconds == 30.0
        assert error.elapsed_seconds == 45.5
        assert error.is_retryable()  # 超时应该是可重试的
        assert "45.50" in error.message
        assert "30.00" in error.message

    def test_checksum_mismatch_error(self):
        """测试 KVChecksumMismatchError"""
        error = KVChecksumMismatchError(
            expected="abc123",
            actual="def456",
            transfer_id="t-789",
        )

        assert error.code == KVErrorCode.CHECKSUM_MISMATCH
        assert error.expected == "abc123"
        assert error.actual == "def456"
        assert "abc123" in error.message
        assert "def456" in error.message

    def test_metadata_mismatch_error(self):
        """测试 KVMetadataMismatchError"""
        error = KVMetadataMismatchError(
            field="num_tokens",
            expected=128,
            actual=256,
        )

        assert error.code == KVErrorCode.METADATA_MISMATCH
        assert error.field == "num_tokens"
        assert error.expected == 128
        assert error.actual == 256
        assert "num_tokens" in error.message


class TestConfigErrors:
    """测试配置错误"""

    def test_config_missing_error(self):
        """测试 KVConfigMissingError"""
        error = KVConfigMissingError(config_key="max_tokens")

        assert error.code == KVErrorCode.CONFIG_MISSING
        assert error.config_key == "max_tokens"
        assert "max_tokens" in error.message

    def test_config_invalid_error(self):
        """测试 KVConfigInvalidError"""
        error = KVConfigInvalidError(
            config_key="batch_size",
            value=-1,
            reason="must be positive",
        )

        assert error.code == KVErrorCode.CONFIG_INVALID
        assert error.config_key == "batch_size"
        assert error.value == -1
        assert "-1" in error.message
        assert "positive" in error.message

    def test_not_implemented_error(self):
        """测试 KVNotImplementedError"""
        error = KVNotImplementedError(feature="async transfer")

        assert error.code == KVErrorCode.NOT_IMPLEMENTED
        assert error.feature == "async transfer"
        assert "async transfer" in error.message
        assert "Fail-Fast" in error.message


class TestErrorCatching:
    """测试错误捕获与处理"""

    def test_catch_by_base_class(self):
        """测试通过基类捕获"""
        with pytest.raises(KVCacheError) as exc_info:
            raise KVBudgetExceededError(requested=100, available=50)

        error = exc_info.value
        assert error.code == KVErrorCode.BUDGET_EXCEEDED

    def test_catch_by_specific_class(self):
        """测试通过具体类捕获"""
        with pytest.raises(KVBudgetExceededError) as exc_info:
            raise KVBudgetExceededError(requested=200, available=100)

        error = exc_info.value
        assert error.requested == 200

    def test_multiple_error_types(self):
        """测试多种错误类型处理"""
        errors = [
            KVBudgetExceededError(requested=100, available=50),
            KVInvalidHandleError(handle_id="h-1"),
            KVNoVictimError(bytes_needed=1024),
            KVTransferFailedError(transfer_id="t-1", source="a", target="b"),
            KVConfigMissingError(config_key="key"),
        ]

        for error in errors:
            assert isinstance(error, KVCacheError)
            assert isinstance(error.code, KVErrorCode)
            assert len(error.message) > 0
            data = error.to_dict()
            assert "code" in data
            assert "message" in data


class TestErrorChaining:
    """测试错误链"""

    def test_error_with_cause(self):
        """测试带原因的错误"""
        original = ValueError("Original error")
        error = KVTransferFailedError(
            transfer_id="t-chain",
            source="src",
            target="dst",
            reason=str(original),
            context={"cause": str(original)},
        )

        assert "Original error" in error.message

    def test_nested_error_handling(self):
        """测试嵌套错误处理"""
        try:
            try:
                raise ValueError("Low level error")
            except ValueError as e:
                raise KVTransferFailedError(
                    transfer_id="t-nested",
                    source="a",
                    target="b",
                    reason=str(e),
                ) from e
        except KVTransferFailedError as error:
            assert error.__cause__ is not None
            assert "Low level error" in str(error.__cause__)
