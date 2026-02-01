"""KV Block memory layout implementations.

This module provides different memory layout strategies for KV cache blocks:
- Contiguous: Single large memory allocation with sequential access
- Chunked: Multiple small memory allocations with indexed access

Each layout has different performance characteristics for allocation speed,
access latency, and memory fragmentation.
"""

from __future__ import annotations

from .base import BaseKVBlock
from .chunked import ChunkedKVBlock
from .contiguous import ContiguousKVBlock

__all__ = ["BaseKVBlock", "ContiguousKVBlock", "ChunkedKVBlock"]
