"""Minimal test to verify SCBench module import and basic functionality."""

import sys
from pathlib import Path

# Add benchmark to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from benchmark.benchmark_scbench import (
            SCBenchBatch,
            SCBenchEvaluator,
            SCBenchPromptor,
            VLLMDirectGenerator,
        )

        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_batch_config():
    """Test SCBenchBatch configuration."""
    print("\nTesting Batch configuration...")

    try:
        from benchmark.benchmark_scbench import SCBenchBatch

        config = {
            "hf_dataset_name": "microsoft/SCBench",
            "hf_dataset_config": "scbench_choice_eng",
            "hf_split": "test",
            "max_samples": 1,
        }

        batch = SCBenchBatch(config)
        print(f"✅ Batch initialized: {batch.task_name}")
        return True
    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        return False


def test_promptor_config():
    """Test SCBenchPromptor configuration."""
    print("\nTesting Promptor configuration...")

    try:
        from benchmark.benchmark_scbench import SCBenchPromptor

        config = {
            "max_input_tokens": 12000,
            "truncation_manner": "middle",
            "use_chat_template": False,
        }

        promptor = SCBenchPromptor(config)
        print(f"✅ Promptor initialized: max_tokens={promptor.max_input_tokens}")
        return True
    except Exception as e:
        print(f"❌ Promptor test failed: {e}")
        return False


def test_evaluator_config():
    """Test SCBenchEvaluator configuration."""
    print("\nTesting Evaluator configuration...")

    try:
        from benchmark.benchmark_scbench import SCBenchEvaluator

        config = {
            "output_dir": "/tmp/scbench_test",
            "model_name": "test-model",
            "task": "scbench_choice_eng",
        }

        evaluator = SCBenchEvaluator(config)
        print(f"✅ Evaluator initialized: output_dir={evaluator.output_dir}")
        return True
    except Exception as e:
        print(f"❌ Evaluator test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SCBench Module Test Suite")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Batch Config", test_batch_config()))
    results.append(("Promptor Config", test_promptor_config()))
    results.append(("Evaluator Config", test_evaluator_config()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")

    sys.exit(0 if total_passed == len(results) else 1)
