# Retrywrap

A flexible and lightweight retry decorator for Python functions.

## Installation

```bash
pip install retrywrap
```

## Quick Start

```python
from retrywrap import retry

# Basic usage with default settings (3 attempts, 1 second delay)
@retry
def fetch_data():
    # Your code here
    pass

# With custom parameters
@retry(attempts=5, delay=0.5, backoff=2, exceptions=(TimeoutError, ConnectionError))
def call_api():
    print("Calling API...")
    raise TimeoutError("API timeout")
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `attempts` | int | 3 | Maximum number of retry attempts |
| `delay` | float | 1 | Initial delay between retries (seconds) |
| `backoff` | float | 1 | Multiplier for delay after each retry |
| `exceptions` | tuple | (Exception,) | Exception types to catch and retry |

## Examples

### Basic Retry

```python
from retrywrap import retry

@retry
def unreliable_function():
    # Will retry 3 times with 1 second delay
    ...
```

### Custom Attempts and Delay

```python
@retry(attempts=5, delay=2)
def slow_service():
    # Will retry 5 times with 2 second delay
    ...
```

### Exponential Backoff

```python
@retry(attempts=4, delay=1, backoff=2)
def api_call():
    # Delays: 1s, 2s, 4s between retries
    ...
```

### Specific Exceptions

```python
@retry(attempts=3, exceptions=(ConnectionError, TimeoutError))
def network_request():
    # Only retries on ConnectionError or TimeoutError
    # Other exceptions will be raised immediately
    ...
```

## License

MIT License - see [LICENSE](LICENSE) for details.
