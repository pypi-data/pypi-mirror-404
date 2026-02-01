"""Tests for KV Transfer Engine MVP implementation.

测试 KV Transfer Engine 与 comm 后端的对接。
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from sagellm_protocol.kv.enums import TransferStatus

from sagellm_kv_cache import KVHandle, KVTransferEngine, KVTransferFailedError


class TestKVTransferEngine:
    """测试 KV Transfer Engine"""

    def test_init_fail_fast_no_backend(self):
        """测试 Fail-Fast：缺少 comm_backend"""
        with pytest.raises(ValueError, match="comm_backend cannot be None"):
            KVTransferEngine(comm_backend=None)

    def test_init_success(self):
        """测试成功初始化"""
        mock_backend = MagicMock()
        engine = KVTransferEngine(comm_backend=mock_backend)

        assert engine._comm_backend is mock_backend
        assert engine.get_pending_count() == 0
        assert engine.get_completed_count() == 0

    def test_transfer_fail_fast_invalid_src_rank(self):
        """测试 Fail-Fast：无效的 src_rank"""
        mock_backend = MagicMock()
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        with pytest.raises(ValueError, match="Invalid src_rank"):
            engine.transfer_kv_handle(handle, src_rank=-1, dst_rank=1)

    def test_transfer_fail_fast_invalid_dst_rank(self):
        """测试 Fail-Fast：无效的 dst_rank"""
        mock_backend = MagicMock()
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        with pytest.raises(ValueError, match="Invalid dst_rank"):
            engine.transfer_kv_handle(handle, src_rank=0, dst_rank=-1)

    def test_transfer_fail_fast_same_rank(self):
        """测试 Fail-Fast：src_rank 和 dst_rank 相同"""
        mock_backend = MagicMock()
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        with pytest.raises(ValueError, match="cannot be the same"):
            engine.transfer_kv_handle(handle, src_rank=0, dst_rank=0)

    def test_transfer_fail_fast_invalid_current_rank(self):
        """测试 Fail-Fast：当前 rank 既不是源也不是目标"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 2
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        with pytest.raises(ValueError, match="neither src.*nor dst"):
            engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1)

    def test_transfer_send_fail_fast_no_tensor(self):
        """测试 Fail-Fast：发送方缺少 tensor"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 0
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        with pytest.raises(KVTransferFailedError, match="tensor is required for sender"):
            engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1, tensor=None)

    def test_transfer_recv_fail_fast_no_tensor(self):
        """测试 Fail-Fast：接收方缺少 tensor buffer"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 1
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        with pytest.raises(KVTransferFailedError, match="tensor buffer is required for receiver"):
            engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1, tensor=None)

    def test_transfer_send_success(self):
        """测试成功发送"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 0
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        mock_tensor = MagicMock()
        transfer_id = engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1, tensor=mock_tensor)

        # 验证发送被调用
        mock_backend.send.assert_called_once_with(mock_tensor, 1)

        # 验证状态
        assert engine.get_pending_count() == 0
        assert engine.get_completed_count() == 1
        assert engine.get_transfer_status(transfer_id) == TransferStatus.COMPLETED

    def test_transfer_recv_success(self):
        """测试成功接收"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 1
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        mock_tensor = MagicMock()
        transfer_id = engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1, tensor=mock_tensor)

        # 验证接收被调用
        mock_backend.recv.assert_called_once_with(mock_tensor, 0)

        # 验证状态
        assert engine.get_pending_count() == 0
        assert engine.get_completed_count() == 1
        assert engine.get_transfer_status(transfer_id) == TransferStatus.COMPLETED

    def test_transfer_send_failure(self):
        """测试发送失败"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 0
        mock_backend.send.side_effect = RuntimeError("Network error")
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        mock_tensor = MagicMock()

        with pytest.raises(KVTransferFailedError, match="failed"):
            engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1, tensor=mock_tensor)

        # 验证失败被记录
        assert engine.get_pending_count() == 0
        assert engine.get_completed_count() == 1

    def test_get_transfer_metadata(self):
        """测试获取传输元数据"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 0
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        mock_tensor = MagicMock()
        transfer_id = engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1, tensor=mock_tensor)

        metadata = engine.get_transfer_metadata(transfer_id)
        assert metadata.transfer_id == transfer_id
        assert metadata.token_start == 0
        assert metadata.token_end == 128

    def test_get_transfer_status_not_found(self):
        """测试获取不存在的传输状态"""
        mock_backend = MagicMock()
        engine = KVTransferEngine(comm_backend=mock_backend)

        with pytest.raises(KeyError, match="not found"):
            engine.get_transfer_status(uuid.uuid4())

    def test_clear_completed(self):
        """测试清理已完成的传输"""
        mock_backend = MagicMock()
        mock_backend.get_rank.return_value = 0
        engine = KVTransferEngine(comm_backend=mock_backend)

        handle = KVHandle(
            handle_id=uuid.uuid4(),
            num_tokens=128,
            token_start=0,
            token_end=128,
        )

        mock_tensor = MagicMock()
        engine.transfer_kv_handle(handle, src_rank=0, dst_rank=1, tensor=mock_tensor)

        assert engine.get_completed_count() == 1

        engine.clear_completed()
        assert engine.get_completed_count() == 0
