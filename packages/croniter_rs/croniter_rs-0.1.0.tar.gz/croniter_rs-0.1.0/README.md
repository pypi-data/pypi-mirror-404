# croniter-rs

[![CI](https://github.com/Souls-R/croniter-rs/actions/workflows/CI.yml/badge.svg)](https://github.com/Souls-R/croniter-rs/actions/workflows/CI.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance Rust implementation of Python's [croniter](https://github.com/kiorky/croniter) library, providing blazing-fast cron expression parsing and iteration.

## Overview

`croniter-rs` is a drop-in replacement for the popular Python `croniter` library, written in Rust using PyO3 for seamless Python integration. It provides the same API while delivering significant performance improvements for cron schedule calculations.

Perfect for applications that need to:
- Calculate thousands of cron schedule occurrences
- Validate cron expressions at scale
- Match datetime objects against cron patterns efficiently
- Iterate through cron schedules with minimal overhead

## Features

- **Drop-in Replacement**: Compatible API with Python's croniter library
- **High Performance**: 15-55x faster than pure Python implementation
- **Full Cron Syntax Support**:
  - Standard 5-field format: `minute hour day month weekday`
  - Extended 6-field format with seconds: `second minute hour day month weekday`
- **Advanced Syntax**:
  - Last day of month: `L`
  - Nth weekday of month: `#` (e.g., `MON#1` for first Monday)
  - Ranges: `1-5`, `MON-FRI`
  - Steps: `*/5`, `1-10/2`
  - Lists: `1,2,3`, `MON,WED,FRI`
  - Month and weekday names: `JAN`, `FEB`, `MON`, `TUE`
  - Hash expressions: `H`, `H(0-30)` (Jenkins-style)
- **Flexible Return Types**: Return datetime objects or Unix timestamps
- **Bidirectional Iteration**: Get next or previous occurrences
- **Pattern Matching**: Check if a datetime matches a cron expression
- **Validation**: Validate cron expressions before use

## Installation

```bash
pip install croniter-rs
```

Requirements:
- Python 3.8 or higher
- No additional dependencies required

## Quick Start

### Basic Usage

```python
from croniter_rs import croniter
from datetime import datetime

# Create a cron iterator
base = datetime(2024, 1, 1, 0, 0)
cron = croniter('*/5 * * * *', base)  # Every 5 minutes

# Get next occurrence
next_time = cron.get_next(datetime)
print(next_time)  # 2024-01-01 00:05:00

# Get next occurrence as timestamp
next_timestamp = cron.get_next(float)
print(next_timestamp)  # 1704067500.0
```

### Iterating Through Occurrences

```python
from croniter_rs import croniter
from datetime import datetime

# Create iterator
cron = croniter('0 0 * * *', datetime(2024, 1, 1))  # Daily at midnight

# Get next 5 occurrences
for i in range(5):
    print(cron.get_next(datetime))

# Or use Python iterator protocol
cron = croniter('0 */6 * * *', datetime(2024, 1, 1))  # Every 6 hours
for time in cron:
    print(time)
    if time > datetime(2024, 1, 7):
        break
```

### Getting Previous Occurrences

```python
from croniter_rs import croniter
from datetime import datetime

cron = croniter('0 0 * * *', datetime(2024, 1, 15))

# Get previous occurrence
prev_time = cron.get_prev(datetime)
print(prev_time)  # 2024-01-14 00:00:00

# Get multiple previous occurrences
prev_times = cron.get_prev_n(5, datetime)
print(prev_times)
```

### Validating Cron Expressions

```python
from croniter_rs import croniter

# Check if expression is valid
if croniter.is_valid('0 0 * * *'):
    print("Valid cron expression")

if not croniter.is_valid('invalid expression'):
    print("Invalid cron expression")
```

### Matching Datetime Against Pattern

```python
from croniter_rs import croniter
from datetime import datetime

# Check if a datetime matches a cron pattern
dt = datetime(2024, 1, 1, 12, 0)

if croniter.match('0 12 * * *', dt):
    print("Datetime matches the pattern")

if not croniter.match('0 0 * * *', dt):
    print("Datetime does not match")
```

## API Compatibility

croniter-rs provides a **drop-in replacement** API for Python croniter. The following table shows the compatibility status:

### Fully Compatible Methods

| Method | Status | Notes |
|--------|--------|-------|
| `croniter(expr, start_time, ...)` | ✅ | Constructor with all parameters |
| `get_next(ret_type)` | ✅ | Get next occurrence |
| `get_prev(ret_type)` | ✅ | Get previous occurrence |
| `get_current(ret_type)` | ✅ | Get current time |
| `set_current(time)` | ✅ | Set current time |
| `next(ret_type)` | ✅ | Alias for `get_next()` |
| `all_next(ret_type)` | ✅ | Returns iterator for forward iteration |
| `all_prev(ret_type)` | ✅ | Returns iterator for backward iteration |
| `iter(ret_type)` | ✅ | Returns iterator |
| `is_valid(expr)` | ✅ | Class method to validate expression |
| `match(expr, dt)` | ✅ | Class method to check if datetime matches |
| `expand(expr)` | ✅ | Class method to expand expression |
| `match_range(expr, start, end)` | ✅ | Check if match exists in time range |
| `expanded` | ✅ | Property returning expanded field values |
| `__iter__` / `__next__` | ✅ | Python iterator protocol |

### Additional Methods (croniter-rs only)

| Method | Description |
|--------|-------------|
| `get_next_n(n, ret_type)` | Get next n occurrences as a list |
| `get_prev_n(n, ret_type)` | Get previous n occurrences as a list |

### Migration Guide

For most use cases, migration is a simple import change:

```python
# Before
from croniter import croniter

# After
from croniter_rs import croniter
```

No other code changes are required for standard usage patterns.

## Benchmarks

Performance comparison between croniter-rs and pure Python croniter:

| Operation | croniter (Python) | croniter-rs (Rust) | Speedup |
|-----------|-------------------|-------------------|---------|
| Constructor | 83.79 μs | 6.09 μs | **13.8x** |
| get_next() | 24.62 μs | 0.52 μs | **47.0x** |
| get_prev() | 24.37 μs | 0.49 μs | **49.9x** |
| is_valid() | 79.77 μs | 5.27 μs | **15.1x** |
| match() | 114.97 μs | 5.85 μs | **19.7x** |
| Complex expression | 28.38 μs | 0.56 μs | **50.7x** |
| Batch 1000 iterations | 24.93 ms | 0.45 ms | **55.3x** |

*Benchmarks run on: Linux 6.8.0, Python 3.10, 10000 iterations per operation*

The performance advantage is especially significant when:
- Calculating many occurrences in a loop (up to **55x faster**)
- Iterating through schedules with `get_next()`/`get_prev()` (**47-50x faster**)
- Validating large numbers of cron expressions (**15x faster**)
- Performing pattern matching on high-frequency data (**20x faster**)

## Behavior Differences from Python croniter

croniter-rs adopts a **semantic equivalence** principle for `day_or` logic, which leads to more consistent and predictable behavior. This section documents the differences and explains the design rationale.

### Background: The `day_or` Logic

According to POSIX cron specification:
- If **both** day-of-month and day-of-week are specified (not `*`), the job runs when **either** condition is met (OR logic)
- If **one** of them is `*`, only the other field is checked

The key question is: **Should ranges that cover all values (like `0-6` for weekday or `1-31` for day) be treated as equivalent to `*`?**

| Interpretation | `0-6` / `1-31` treated as | Behavior |
|----------------|---------------------------|----------|
| **Strict** | Explicit range (not `*`) | Triggers `day_or` logic |
| **Semantic** | Equivalent to `*` | Does NOT trigger `day_or` logic |

**croniter-rs uses semantic interpretation consistently**, while **Python croniter is inconsistent** (uses strict for weekday, semantic for day).

### Difference 1: Weekday Full Range (0-6, sun-sat)

When weekday covers all days (`0-6`, `sun-sat`), croniter-rs treats it as equivalent to `*`.

```python
from datetime import datetime

# Expression: Run at midnight on the 15th of each month
# weekday=0-6 covers all days, semantically equivalent to *

expr1 = '0 0 15 * *'      # weekday = * (wildcard)
expr2 = '0 0 15 * 0-6'    # weekday = 0-6 (all days)

start = datetime(2024, 1, 1)  # January 1st is Monday

# Python croniter results:
#   expr1 → 2024-01-15 (Mon) ✓ Correct
#   expr2 → 2024-01-01 (Mon) ✗ Wrong - day_or triggered incorrectly

# croniter-rs results:
#   expr1 → 2024-01-15 (Mon) ✓ Correct
#   expr2 → 2024-01-15 (Mon) ✓ Correct - 0-6 treated as *
```

### Difference 2: Day Full Range (1-31)

When day-of-month covers all days (`1-31`), croniter-rs treats it as equivalent to `*`.

```python
from datetime import datetime

# Expression: Run at midnight on Sun/Tue/Thu in April
# day=1-31 covers all days, semantically equivalent to *

expr1 = '0 0 * 4 0,2,4'     # day = * (wildcard)
expr2 = '0 0 1-31 4 0,2,4'  # day = 1-31 (all days)

start = datetime(2024, 1, 1)

# Python croniter results:
#   expr1 → 2024-04-02 (Tue) ✓ Correct
#   expr2 → 2024-04-01 (Mon) ✗ Wrong - ignores weekday constraint

# croniter-rs results:
#   expr1 → 2024-04-02 (Tue) ✓ Correct
#   expr2 → 2024-04-02 (Tue) ✓ Correct - 1-31 treated as *
```

### Compatibility Note

These differences affect approximately **0.3-0.5%** of randomly generated complex cron expressions. Common cron patterns (like `0 0 * * *`, `*/5 * * * *`, `0 9 * * 1-5`) are 100% compatible.

## Known Limitations

1. **7-field format (year field)**: Not yet supported.

2. **Word aliases**: Special aliases like `@hourly`, `@daily`, `@weekly`, `@monthly`, `@yearly`, and `@reboot` are not yet implemented.

3. **Timezone support**: Currently uses naive datetime objects.

## Exception Types

croniter-rs provides the same exception types as the original croniter:

- `CroniterBadCronError`: Invalid cron expression syntax
- `CroniterBadDateError`: Invalid date/time value
- `CroniterNotAlphaError`: Invalid alphabetic value in expression
- `CroniterUnsupportedSyntaxError`: Unsupported cron syntax feature

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original [croniter](https://github.com/kiorky/croniter) library by kiorky
- Built with [PyO3](https://github.com/PyO3/pyo3) for Rust-Python interoperability
