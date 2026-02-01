"""
Comprehensive benchmark suite for croniter-rs vs croniter

This benchmark compares the performance of croniter_rs (Rust implementation)
against the original croniter (Python implementation).

Install dependencies:
    pip install pytest-benchmark croniter

Run benchmarks:
    pytest tests/test_benchmark.py --benchmark-only
    pytest tests/test_benchmark.py --benchmark-only --benchmark-compare
"""

import pytest
from datetime import datetime
import sys

# Import both implementations
try:
    from croniter_rs import croniter as croniter_rust
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("Warning: croniter_rs not available. Build it first with 'maturin develop'")

try:
    from croniter import croniter as croniter_python
    PYTHON_AVAILABLE = True
except ImportError:
    PYTHON_AVAILABLE = False
    print("Warning: croniter not available. Install it with 'pip install croniter'")


# Test expressions
SIMPLE_EXPRESSIONS = [
    "*/5 * * * *",      # Every 5 minutes
    "0 0 * * *",        # Daily at midnight
    "0 12 * * *",       # Daily at noon
]

COMPLEX_EXPRESSIONS = [
    "0 0 1,15 * mon-fri",       # 1st and 15th of month, weekdays only
    "*/15 9-17 * * 1-5",        # Every 15 min, 9am-5pm, Mon-Fri
    "0 0,12 * * *",             # Twice daily
    "*/10 * * * *",             # Every 10 minutes
]

VALID_EXPRESSIONS = [
    "* * * * *",
    "0 0 * * *",
    "*/5 * * * *",
    "0 0 1 * *",
    "0 0 * * 0",
    "0 0 1,15 * *",
]

INVALID_EXPRESSIONS = [
    "* * * *",          # Too few fields
    "60 * * * *",       # Invalid minute
    "* 24 * * *",       # Invalid hour
    "* * 32 * *",       # Invalid day
    "* * * 13 *",       # Invalid month
    "* * * * 7",        # Invalid weekday (depends on implementation)
    "invalid",          # Not a cron expression
]

# Base datetime for consistent testing
BASE_DATETIME = datetime(2024, 1, 1, 0, 0, 0)


# ============================================================================
# SIMPLE EXPRESSIONS BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", SIMPLE_EXPRESSIONS)
def test_simple_rust_creation(benchmark, expr):
    """Benchmark: Object creation with simple expressions (Rust)"""
    benchmark.group = f"simple_creation_{expr}"
    benchmark(croniter_rust, expr, BASE_DATETIME)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", SIMPLE_EXPRESSIONS)
def test_simple_python_creation(benchmark, expr):
    """Benchmark: Object creation with simple expressions (Python)"""
    benchmark.group = f"simple_creation_{expr}"
    benchmark(croniter_python, expr, BASE_DATETIME)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", SIMPLE_EXPRESSIONS)
def test_simple_rust_get_next_single(benchmark, expr):
    """Benchmark: Single get_next() call with simple expressions (Rust)"""
    benchmark.group = f"simple_get_next_single_{expr}"

    def run():
        cron = croniter_rust(expr, BASE_DATETIME)
        return cron.get_next(float)

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", SIMPLE_EXPRESSIONS)
def test_simple_python_get_next_single(benchmark, expr):
    """Benchmark: Single get_next() call with simple expressions (Python)"""
    benchmark.group = f"simple_get_next_single_{expr}"

    def run():
        cron = croniter_python(expr, BASE_DATETIME)
        return cron.get_next(float)

    benchmark(run)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", SIMPLE_EXPRESSIONS)
def test_simple_rust_get_next_100(benchmark, expr):
    """Benchmark: 100 get_next() iterations with simple expressions (Rust)"""
    benchmark.group = f"simple_get_next_100_{expr}"

    def run():
        cron = croniter_rust(expr, BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next(float))
        return results

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", SIMPLE_EXPRESSIONS)
def test_simple_python_get_next_100(benchmark, expr):
    """Benchmark: 100 get_next() iterations with simple expressions (Python)"""
    benchmark.group = f"simple_get_next_100_{expr}"

    def run():
        cron = croniter_python(expr, BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next(float))
        return results

    benchmark(run)


# ============================================================================
# COMPLEX EXPRESSIONS BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", COMPLEX_EXPRESSIONS)
def test_complex_rust_creation(benchmark, expr):
    """Benchmark: Object creation with complex expressions (Rust)"""
    benchmark.group = f"complex_creation_{expr}"
    benchmark(croniter_rust, expr, BASE_DATETIME)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", COMPLEX_EXPRESSIONS)
def test_complex_python_creation(benchmark, expr):
    """Benchmark: Object creation with complex expressions (Python)"""
    benchmark.group = f"complex_creation_{expr}"
    benchmark(croniter_python, expr, BASE_DATETIME)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", COMPLEX_EXPRESSIONS)
def test_complex_rust_get_next_single(benchmark, expr):
    """Benchmark: Single get_next() call with complex expressions (Rust)"""
    benchmark.group = f"complex_get_next_single_{expr}"

    def run():
        cron = croniter_rust(expr, BASE_DATETIME)
        return cron.get_next(float)

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", COMPLEX_EXPRESSIONS)
def test_complex_python_get_next_single(benchmark, expr):
    """Benchmark: Single get_next() call with complex expressions (Python)"""
    benchmark.group = f"complex_get_next_single_{expr}"

    def run():
        cron = croniter_python(expr, BASE_DATETIME)
        return cron.get_next(float)

    benchmark(run)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", COMPLEX_EXPRESSIONS)
def test_complex_rust_get_next_100(benchmark, expr):
    """Benchmark: 100 get_next() iterations with complex expressions (Rust)"""
    benchmark.group = f"complex_get_next_100_{expr}"

    def run():
        cron = croniter_rust(expr, BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next(float))
        return results

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", COMPLEX_EXPRESSIONS)
def test_complex_python_get_next_100(benchmark, expr):
    """Benchmark: 100 get_next() iterations with complex expressions (Python)"""
    benchmark.group = f"complex_get_next_100_{expr}"

    def run():
        cron = croniter_python(expr, BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next(float))
        return results

    benchmark(run)


# ============================================================================
# GET_PREV BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
def test_rust_get_prev_single(benchmark):
    """Benchmark: Single get_prev() call (Rust)"""
    benchmark.group = "get_prev_single"

    def run():
        cron = croniter_rust("*/5 * * * *", BASE_DATETIME)
        return cron.get_prev(float)

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
def test_python_get_prev_single(benchmark):
    """Benchmark: Single get_prev() call (Python)"""
    benchmark.group = "get_prev_single"

    def run():
        cron = croniter_python("*/5 * * * *", BASE_DATETIME)
        return cron.get_prev(float)

    benchmark(run)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
def test_rust_get_prev_100(benchmark):
    """Benchmark: 100 get_prev() iterations (Rust)"""
    benchmark.group = "get_prev_100"

    def run():
        cron = croniter_rust("*/5 * * * *", BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_prev(float))
        return results

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
def test_python_get_prev_100(benchmark):
    """Benchmark: 100 get_prev() iterations (Python)"""
    benchmark.group = "get_prev_100"

    def run():
        cron = croniter_python("*/5 * * * *", BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_prev(float))
        return results

    benchmark(run)


# ============================================================================
# IS_VALID BENCHMARKS
# ============================================================================

@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", VALID_EXPRESSIONS)
def test_rust_is_valid_valid(benchmark, expr):
    """Benchmark: is_valid() with valid expressions (Rust)"""
    benchmark.group = f"is_valid_valid_{expr}"
    benchmark(croniter_rust.is_valid, expr)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", VALID_EXPRESSIONS)
def test_python_is_valid_valid(benchmark, expr):
    """Benchmark: is_valid() with valid expressions (Python)"""
    benchmark.group = f"is_valid_valid_{expr}"
    benchmark(croniter_python.is_valid, expr)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr", INVALID_EXPRESSIONS)
def test_rust_is_valid_invalid(benchmark, expr):
    """Benchmark: is_valid() with invalid expressions (Rust)"""
    benchmark.group = f"is_valid_invalid_{expr}"
    benchmark(croniter_rust.is_valid, expr)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr", INVALID_EXPRESSIONS)
def test_python_is_valid_invalid(benchmark, expr):
    """Benchmark: is_valid() with invalid expressions (Python)"""
    benchmark.group = f"is_valid_invalid_{expr}"
    benchmark(croniter_python.is_valid, expr)


# ============================================================================
# MATCH BENCHMARKS
# ============================================================================

MATCH_TEST_CASES = [
    ("*/5 * * * *", datetime(2024, 1, 1, 0, 0, 0), True),   # Should match
    ("*/5 * * * *", datetime(2024, 1, 1, 0, 5, 0), True),   # Should match
    ("*/5 * * * *", datetime(2024, 1, 1, 0, 3, 0), False),  # Should not match
    ("0 0 * * *", datetime(2024, 1, 1, 0, 0, 0), True),     # Should match
    ("0 0 * * *", datetime(2024, 1, 1, 12, 0, 0), False),   # Should not match
]


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
@pytest.mark.parametrize("expr,dt,expected", MATCH_TEST_CASES)
def test_rust_match(benchmark, expr, dt, expected):
    """Benchmark: match() method (Rust)"""
    benchmark.group = f"match_{expr}_{expected}"
    result = benchmark(croniter_rust.match, expr, dt)
    assert result == expected


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
@pytest.mark.parametrize("expr,dt,expected", MATCH_TEST_CASES)
def test_python_match(benchmark, expr, dt, expected):
    """Benchmark: match() method (Python)"""
    benchmark.group = f"match_{expr}_{expected}"
    result = benchmark(croniter_python.match, expr, dt)
    assert result == expected


# ============================================================================
# OBJECT CREATION OVERHEAD
# ============================================================================

@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
def test_rust_creation_overhead(benchmark):
    """Benchmark: Object creation overhead (Rust)"""
    benchmark.group = "creation_overhead"
    benchmark(croniter_rust, "*/5 * * * *", BASE_DATETIME)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
def test_python_creation_overhead(benchmark):
    """Benchmark: Object creation overhead (Python)"""
    benchmark.group = "creation_overhead"
    benchmark(croniter_python, "*/5 * * * *", BASE_DATETIME)


# ============================================================================
# COMBINED OPERATIONS
# ============================================================================

@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
def test_rust_combined_operations(benchmark):
    """Benchmark: Combined operations - create, get_next, get_prev (Rust)"""
    benchmark.group = "combined_operations"

    def run():
        cron = croniter_rust("*/5 * * * *", BASE_DATETIME)
        next_times = [cron.get_next(float) for _ in range(10)]
        prev_times = [cron.get_prev(float) for _ in range(10)]
        return next_times, prev_times

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
def test_python_combined_operations(benchmark):
    """Benchmark: Combined operations - create, get_next, get_prev (Python)"""
    benchmark.group = "combined_operations"

    def run():
        cron = croniter_python("*/5 * * * *", BASE_DATETIME)
        next_times = [cron.get_next(float) for _ in range(10)]
        prev_times = [cron.get_prev(float) for _ in range(10)]
        return next_times, prev_times

    benchmark(run)


# ============================================================================
# DATETIME VS FLOAT RETURN TYPE
# ============================================================================

@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
def test_rust_return_datetime(benchmark):
    """Benchmark: get_next() returning datetime (Rust)"""
    benchmark.group = "return_type_datetime"

    def run():
        cron = croniter_rust("*/5 * * * *", BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next())
        return results

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
def test_python_return_datetime(benchmark):
    """Benchmark: get_next() returning datetime (Python)"""
    benchmark.group = "return_type_datetime"

    def run():
        cron = croniter_python("*/5 * * * *", BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next())
        return results

    benchmark(run)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="croniter_rs not available")
def test_rust_return_float(benchmark):
    """Benchmark: get_next() returning float (Rust)"""
    benchmark.group = "return_type_float"

    def run():
        cron = croniter_rust("*/5 * * * *", BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next(float))
        return results

    benchmark(run)


@pytest.mark.skipif(not PYTHON_AVAILABLE, reason="croniter not available")
def test_python_return_float(benchmark):
    """Benchmark: get_next() returning float (Python)"""
    benchmark.group = "return_type_float"

    def run():
        cron = croniter_python("*/5 * * * *", BASE_DATETIME)
        results = []
        for _ in range(100):
            results.append(cron.get_next(float))
        return results

    benchmark(run)


# ============================================================================
# SUMMARY REPORT
# ============================================================================

def test_benchmark_summary(benchmark):
    """
    This test doesn't benchmark anything, but prints a summary message.

    To see detailed benchmark results with statistics, run:
        pytest tests/test_benchmark.py --benchmark-only -v

    To compare results and see speedup ratios:
        pytest tests/test_benchmark.py --benchmark-only --benchmark-compare

    To save results for later comparison:
        pytest tests/test_benchmark.py --benchmark-only --benchmark-save=baseline

    To compare against saved baseline:
        pytest tests/test_benchmark.py --benchmark-only --benchmark-compare=baseline

    For histogram output:
        pytest tests/test_benchmark.py --benchmark-only --benchmark-histogram
    """
    benchmark.group = "summary"
    benchmark(lambda: None)


if __name__ == "__main__":
    print("=" * 80)
    print("Croniter-rs Benchmark Suite")
    print("=" * 80)
    print()
    print("This benchmark suite compares croniter_rs (Rust) vs croniter (Python)")
    print()
    print("Test Categories:")
    print("  1. Simple expressions: */5 * * * *, 0 0 * * *")
    print("  2. Complex expressions: 0 0 1,15 * mon-fri, */15 9-17 * * 1-5")
    print("  3. get_next() - single call")
    print("  4. get_next() - 100 iterations")
    print("  5. get_prev() - single call")
    print("  6. get_prev() - 100 iterations")
    print("  7. is_valid() - valid expressions")
    print("  8. is_valid() - invalid expressions")
    print("  9. match() - matching datetime")
    print(" 10. Object creation overhead")
    print()
    print("Run with: pytest tests/test_benchmark.py --benchmark-only")
    print("=" * 80)
