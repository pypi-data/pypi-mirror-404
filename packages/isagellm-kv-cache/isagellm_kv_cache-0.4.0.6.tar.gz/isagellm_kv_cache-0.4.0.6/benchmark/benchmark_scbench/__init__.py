"""SCBench (Shared Context Benchmark) integration for SAGE.

SCBench evaluates long-context LLMs' ability to handle shared context across
multiple queries or turns. It supports two evaluation modes:

1. Multi-Turn: Simulates conversation history accumulation with golden answers
2. SCDQ (Same Context Different Query): Simulates KV cache reuse scenarios

Key Features:
- Middle Truncation: 128K token truncation strategy
- Refiner Support: Seamless integration with sageRefiner compression algorithms
- Original Scoring: 100% alignment with SCBench paper metrics
"""

from .batch import SCBenchBatch
from .evaluator import SCBenchEvaluator
from .promptor import SCBenchPromptor
from .vllm_direct_generator import VLLMDirectGenerator

__all__ = [
    "SCBenchBatch",
    "SCBenchPromptor",
    "SCBenchEvaluator",
    "VLLMDirectGenerator",
]
