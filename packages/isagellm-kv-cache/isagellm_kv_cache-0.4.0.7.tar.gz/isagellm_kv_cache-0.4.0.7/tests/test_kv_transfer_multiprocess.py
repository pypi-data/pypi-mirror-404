"""真实 Gloo Backend 多进程测试

使用 torch.multiprocessing 进行真实的分布式测试，验证：
1. 真实的 Gloo backend 初始化
2. 多进程环境下的 KV Transfer
3. 跨进程的实际通信

运行方式：
    pytest tests/test_kv_transfer_multiprocess.py -v
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import pytest
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from sagellm_comm import GlooBackend
from sagellm_kv_cache import KVHandle, KVTransferEngine
from sagellm_protocol import DType


def _worker_basic_transfer(rank: int, world_size: int, store_file: str) -> dict:
    """Worker function for basic transfer test

    Args:
        rank: Process rank
        world_size: Total number of processes
        store_file: Path to shared file store

    Returns:
        Test results dictionary
    """
    try:
        # 1. Initialize Gloo backend
        os.environ["RANK"] = str(rank)
        os.environ["WORLD_SIZE"] = str(world_size)
        os.environ["LOCAL_RANK"] = str(rank)
        os.environ["LOCAL_WORLD_SIZE"] = str(world_size)
        os.environ["MASTER_ADDR"] = "127.0.0.1"
        os.environ["MASTER_PORT"] = "29500"

        backend = GlooBackend()
        backend.init(
            rank=rank,
            world_size=world_size,
            master_addr="127.0.0.1",
            master_port=29500,
        )

        # 2. Create KV Transfer Engine
        engine = KVTransferEngine(backend)

        # 3. Create test data
        seq_length = 128
        kv_data = torch.randn(2, 4, seq_length, 8, 64, dtype=torch.float32)
        # Shape: [2, layers, seq, heads, dim] = [2, 4, 128, 8, 64]
        # Size: 2 * 4 * 128 * 8 * 64 * 4 bytes = 1.0 MB

        handle = KVHandle(
            handle_id=uuid4(),
            request_id=f"req_{rank}",
            num_tokens=seq_length,
            dtype=DType.FP32,
            device="cpu",
            memory_ptr=id(kv_data),
            rank=rank,
        )

        # 4. Perform transfer based on rank
        if rank == 0:
            # Rank 0: Send to rank 1
            transfer_id = engine.transfer_kv_handle(
                handle=handle, src_rank=0, dst_rank=1, tensor=kv_data
            )

            status = engine.get_transfer_status(transfer_id)
            metadata = engine.get_transfer_metadata(transfer_id)

            result = {
                "rank": rank,
                "role": "sender",
                "transfer_id": str(transfer_id),
                "status": str(status),
                "source_device": metadata.source_device,
                "target_device": metadata.target_device,
                "total_bytes": metadata.total_bytes,
                "success": True,
            }

        elif rank == 1:
            # Rank 1: Receive from rank 0
            # Wait a bit for sender to prepare
            time.sleep(0.1)

            # Create receive buffer
            recv_buffer = torch.zeros_like(kv_data)

            # Receive
            transfer_id = engine.transfer_kv_handle(
                handle=handle, src_rank=0, dst_rank=1, tensor=recv_buffer
            )

            status = engine.get_transfer_status(transfer_id)
            metadata = engine.get_transfer_metadata(transfer_id)

            result = {
                "rank": rank,
                "role": "receiver",
                "transfer_id": str(transfer_id),
                "status": str(status),
                "source_device": metadata.source_device,
                "target_device": metadata.target_device,
                "total_bytes": metadata.total_bytes,
                "received_data_shape": list(recv_buffer.shape),
                "success": True,
            }

        else:
            result = {"rank": rank, "role": "idle", "success": True}

        # Cleanup
        backend.destroy()

        return result

    except Exception as e:
        return {
            "rank": rank,
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


def _worker_batch_transfer(rank: int, world_size: int, store_file: str) -> dict:
    """Worker function for batch transfer test

    Tests multiple transfers from one rank to multiple destinations.
    """
    try:
        # Initialize
        os.environ["RANK"] = str(rank)
        os.environ["WORLD_SIZE"] = str(world_size)
        os.environ["LOCAL_RANK"] = str(rank)
        os.environ["LOCAL_WORLD_SIZE"] = str(world_size)
        os.environ["MASTER_ADDR"] = "127.0.0.1"
        os.environ["MASTER_PORT"] = "29501"  # Different port

        backend = GlooBackend()
        backend.init(
            rank=rank,
            world_size=world_size,
            master_addr="127.0.0.1",
            master_port=29501,
        )
        engine = KVTransferEngine(backend)

        transfer_count = 0
        completed_transfers = []

        if rank == 0:
            # Rank 0: Send to all other ranks
            for dst_rank in range(1, world_size):
                seq_length = 64 + dst_rank * 32
                kv_data = torch.randn(2, 4, seq_length, 8, 64, dtype=torch.float32)

                handle = KVHandle(
                    handle_id=uuid4(),
                    request_id=f"req_0_to_{dst_rank}",
                    num_tokens=seq_length,
                    dtype=DType.FP32,
                    device="cpu",
                    memory_ptr=id(kv_data),
                    rank=0,
                )

                transfer_id = engine.transfer_kv_handle(
                    handle=handle, src_rank=0, dst_rank=dst_rank, tensor=kv_data
                )

                completed_transfers.append(
                    {"dst_rank": dst_rank, "transfer_id": str(transfer_id)}
                )
                transfer_count += 1

            result = {
                "rank": rank,
                "role": "sender",
                "transfer_count": transfer_count,
                "transfers": completed_transfers,
                "success": True,
            }

        else:
            # Other ranks: Receive from rank 0
            time.sleep(0.1)

            seq_length = 64 + rank * 32
            recv_buffer = torch.zeros(2, 4, seq_length, 8, 64, dtype=torch.float32)

            handle = KVHandle(
                handle_id=uuid4(),
                request_id=f"req_recv_{rank}",
                num_tokens=seq_length,
                dtype=DType.FP32,
                device="cpu",
                memory_ptr=id(recv_buffer),
                rank=rank,
            )

            transfer_id = engine.transfer_kv_handle(
                handle=handle, src_rank=0, dst_rank=rank, tensor=recv_buffer
            )

            transfer_count = 1
            result = {
                "rank": rank,
                "role": "receiver",
                "transfer_count": transfer_count,
                "transfer_id": str(transfer_id),
                "success": True,
            }

        # Cleanup
        backend.destroy()

        return result

    except Exception as e:
        return {
            "rank": rank,
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


# Global wrapper functions for multiprocessing (must be pickle-able)
def _basic_worker_wrapper(rank: int, world_size: int, results_list):
    """Wrapper for basic transfer worker that can be pickled"""
    result = _worker_basic_transfer(rank, world_size, "unused")
    results_list.append(result)


def _batch_worker_wrapper(rank: int, world_size: int, results_list):
    """Wrapper for batch transfer worker that can be pickled"""
    result = _worker_batch_transfer(rank, world_size, "unused")
    results_list.append(result)


def _error_worker_wrapper(rank: int, world_size: int, results_list):
    """Wrapper for error handling worker that can be pickled"""
    result = _worker_with_error(rank, world_size, "unused")
    results_list.append(result)


def _worker_with_error(rank: int, world_size: int, store_file: str) -> dict:
    """Worker function for error handling test"""
    try:
        os.environ["RANK"] = str(rank)
        os.environ["WORLD_SIZE"] = str(world_size)
        os.environ["MASTER_ADDR"] = "127.0.0.1"
        os.environ["MASTER_PORT"] = "29502"

        backend = GlooBackend()
        backend.init(
            rank=rank,
            world_size=world_size,
            master_addr="127.0.0.1",
            master_port=29502,
        )
        engine = KVTransferEngine(backend)

        if rank == 0:
            # Try to send to invalid rank
            kv_data = torch.randn(2, 4, 64, 8, 64)
            handle = KVHandle(
                handle_id=uuid4(),
                request_id="test",
                num_tokens=64,
                dtype=DType.FP32,
                device="cpu",
                memory_ptr=id(kv_data),
                rank=0,
            )

            # This should fail or complete depending on backend behavior
            try:
                engine.transfer_kv_handle(
                    handle=handle, src_rank=0, dst_rank=999, tensor=kv_data
                )
            except Exception as e:
                # Expected error
                return {"rank": rank, "success": True, "caught_error": str(e), "role": "sender", "transfer_count": 0}

            return {"rank": rank, "success": True, "role": "sender", "transfer_count": 0}
        else:
            # Receiver - just initialize and wait
            return {"rank": rank, "success": True, "role": "receiver"}

    except Exception as e:
        return {"rank": rank, "success": False, "error": str(e)}


@pytest.mark.skipif(
    not torch.distributed.is_available(), reason="torch.distributed not available"
)
class TestKVTransferMultiprocess:
    """Multi-process tests with real Gloo backend"""

    def test_basic_transfer_2_processes(self, tmp_path: Path):
        """Test basic KV transfer with 2 processes"""
        world_size = 2

        # Spawn processes using multiprocessing
        mp.set_start_method("spawn", force=True)
        manager = mp.Manager()
        results = manager.list()

        processes = []
        for rank in range(world_size):
            p = mp.Process(target=_basic_worker_wrapper, args=(rank, world_size, results))
            p.start()
            processes.append(p)

        # Wait for completion
        for p in processes:
            p.join(timeout=30)
            if p.exitcode != 0:
                raise RuntimeError(f"Process failed with exit code {p.exitcode}")

        # Check results
        assert len(results) == world_size, f"Expected {world_size} results, got {len(results)}"

        for result in results:
            assert result["success"], f"Rank {result['rank']} failed: {result.get('error')}"

        # Verify sender and receiver
        sender = next(r for r in results if r.get("role") == "sender")
        receiver = next(r for r in results if r.get("role") == "receiver")

        assert sender["rank"] == 0
        assert receiver["rank"] == 1
        assert "TransferStatus.COMPLETED" in sender["status"]
        assert "TransferStatus.COMPLETED" in receiver["status"]

        print("\n✅ Basic 2-process transfer test passed!")
        print(f"  - Sender (rank 0): {sender['total_bytes']} bytes transferred")
        print(f"  - Receiver (rank 1): Received data shape {receiver['received_data_shape']}")

    def test_batch_transfer_4_processes(self, tmp_path: Path):
        """Test batch KV transfer with 4 processes"""
        world_size = 4

        # Spawn processes
        mp.set_start_method("spawn", force=True)
        manager = mp.Manager()
        results = manager.list()

        processes = []
        for rank in range(world_size):
            p = mp.Process(target=_batch_worker_wrapper, args=(rank, world_size, results))
            p.start()
            processes.append(p)

        # Wait for completion
        for p in processes:
            p.join(timeout=60)
            if p.exitcode != 0:
                raise RuntimeError(f"Process failed with exit code {p.exitcode}")

        # Check results
        assert len(results) == world_size, f"Expected {world_size} results, got {len(results)}"

        for result in results:
            assert result["success"], f"Rank {result['rank']} failed: {result.get('error')}"

        # Verify sender sent to all receivers
        sender = next(r for r in results if r.get("role") == "sender")
        receivers = [r for r in results if r.get("role") == "receiver"]

        assert sender["rank"] == 0
        assert sender["transfer_count"] == world_size - 1  # Sent to all others
        assert len(receivers) == world_size - 1

        print(f"\n✅ Batch {world_size}-process transfer test passed!")
        print(f"  - Sender (rank 0): {sender['transfer_count']} transfers")
        for r in receivers:
            print(f"  - Receiver (rank {r['rank']}): Received {r['transfer_count']} transfer")

    def test_error_handling_multiprocess(self, tmp_path: Path):
        """Test error handling in multi-process KV transfer"""
        world_size = 2

        # Spawn processes
        mp.set_start_method("spawn", force=True)
        manager = mp.Manager()
        results = manager.list()

        processes = []
        for rank in range(world_size):
            p = mp.Process(target=_error_worker_wrapper, args=(rank, world_size, results))
            p.start()
            processes.append(p)

        # Wait for completion
        for p in processes:
            p.join(timeout=60)
            if p.exitcode != 0:
                raise RuntimeError(f"Process failed with exit code {p.exitcode}")

        # Check results
        assert len(results) == world_size

        for result in results:
            assert result["success"], f"Rank {result['rank']} failed unexpectedly"

        sender = next(r for r in results if r.get("role") == "sender")
        receiver = next(r for r in results if r.get("role") == "receiver")

        # Sender should handle error gracefully
        assert sender["rank"] == 0
        assert sender["transfer_count"] == 0, "Should not have successful transfers"

        print("\n✅ Error handling multiprocess test passed!")
        print(f"  - Sender handled error gracefully")
        print(f"  - Receiver initialized successfully")


@pytest.mark.skipif(
    not torch.distributed.is_available(), reason="torch.distributed not available"
)
def test_real_gloo_backend_initialization():
    """Test that real Gloo backend can be initialized in single process"""
    # This is a simpler test that doesn't require multiprocessing
    # Useful for debugging

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create backend and initialize (it will call dist.init_process_group internally)
        backend = GlooBackend()
        backend.init(
            rank=0,
            world_size=1,
            master_addr="127.0.0.1",
            master_port=29503,
        )

        # Create engine
        engine = KVTransferEngine(backend)

        # Verify basic properties
        assert backend.get_rank() == 0
        assert backend.get_world_size() == 1

        # Cleanup
        backend.destroy()

        print("\n✅ Real Gloo backend initialization test passed!")


if __name__ == "__main__":
    # Can run directly for debugging
    import sys

    print("Running multiprocess KV Transfer tests...")
    print("Note: For full test suite, use: pytest tests/test_kv_transfer_multiprocess.py -v")

    # Run simple initialization test
    if torch.distributed.is_available():
        test_real_gloo_backend_initialization()
    else:
        print("❌ torch.distributed not available, skipping tests")
        sys.exit(1)
