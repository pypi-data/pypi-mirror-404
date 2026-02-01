"""
Comprehensive tests for the retrywrap decorator.
"""

import pytest
import time
from retrywrap import retry


class TestBasicRetry:
    """Test basic retry functionality."""

    def test_successful_function_no_retry_needed(self):
        """Function that succeeds should not retry."""
        call_count = 0

        @retry
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_function_fails_then_succeeds(self):
        """Function that fails initially but succeeds later."""
        call_count = 0

        @retry(attempts=3, delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet!")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_function_exhausts_all_attempts(self):
        """Function that fails all attempts should raise last exception."""
        call_count = 0

        @retry(attempts=3, delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count}")

        with pytest.raises(ValueError, match="Attempt 3"):
            always_fails()
        assert call_count == 3


class TestDecoratorSyntax:
    """Test different decorator syntax options."""

    def test_retry_without_parentheses(self):
        """@retry without parentheses should use defaults."""
        call_count = 0

        @retry
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        result = func()
        assert result == "ok"
        assert call_count == 2

    def test_retry_with_empty_parentheses(self):
        """@retry() should work same as @retry."""
        call_count = 0

        @retry()
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        result = func()
        assert result == "ok"

    def test_retry_with_parameters(self):
        """@retry(attempts=N) should respect parameters."""
        call_count = 0

        @retry(attempts=5, delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise ValueError("fail")
            return "ok"

        result = func()
        assert result == "ok"
        assert call_count == 4


class TestExceptionFiltering:
    """Test exception filtering behavior."""

    def test_catches_specified_exceptions(self):
        """Should retry only on specified exceptions."""
        call_count = 0

        @retry(attempts=3, delay=0.01, exceptions=(ValueError,))
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("retry this")
            return "ok"

        result = func()
        assert result == "ok"
        assert call_count == 3

    def test_does_not_catch_unspecified_exceptions(self):
        """Should not retry on exceptions not in the filter."""
        call_count = 0

        @retry(attempts=3, delay=0.01, exceptions=(ValueError,))
        def func():
            nonlocal call_count
            call_count += 1
            raise TypeError("don't retry this")

        with pytest.raises(TypeError):
            func()
        assert call_count == 1

    def test_multiple_exception_types(self):
        """Should handle multiple exception types."""
        call_count = 0

        @retry(attempts=4, delay=0.01, exceptions=(ValueError, TypeError))
        def func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("first")
            elif call_count == 2:
                raise TypeError("second")
            return "ok"

        result = func()
        assert result == "ok"
        assert call_count == 3


class TestBackoff:
    """Test exponential backoff behavior."""

    def test_exponential_backoff(self):
        """Delay should increase exponentially with backoff multiplier."""
        call_count = 0
        timestamps = []

        @retry(attempts=4, delay=0.1, backoff=2)
        def func():
            nonlocal call_count
            timestamps.append(time.time())
            call_count += 1
            if call_count < 4:
                raise ValueError("retry")
            return "ok"

        result = func()
        assert result == "ok"
        assert call_count == 4

        # Check delays are approximately correct
        # Delay 1: 0.1s, Delay 2: 0.2s, Delay 3: 0.4s
        if len(timestamps) >= 4:
            delay1 = timestamps[1] - timestamps[0]
            delay2 = timestamps[2] - timestamps[1]
            delay3 = timestamps[3] - timestamps[2]
            assert delay1 < delay2 < delay3


class TestFunctionMetadata:
    """Test that function metadata is preserved."""

    def test_preserves_function_name(self):
        """Decorated function should preserve __name__."""
        @retry
        def my_function():
            """My docstring."""
            pass

        assert my_function.__name__ == "my_function"

    def test_preserves_docstring(self):
        """Decorated function should preserve __doc__."""
        @retry
        def my_function():
            """My docstring."""
            pass

        assert my_function.__doc__ == "My docstring."


class TestFunctionArguments:
    """Test that function arguments are passed correctly."""

    def test_positional_args(self):
        """Positional arguments should be passed through."""
        @retry(attempts=2, delay=0.01)
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_keyword_args(self):
        """Keyword arguments should be passed through."""
        @retry(attempts=2, delay=0.01)
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        assert greet("World") == "Hello, World!"
        assert greet("World", greeting="Hi") == "Hi, World!"

    def test_args_preserved_across_retries(self):
        """Arguments should be the same on each retry."""
        call_count = 0
        received_args = []

        @retry(attempts=3, delay=0.01)
        def func(x, y):
            nonlocal call_count
            received_args.append((x, y))
            call_count += 1
            if call_count < 3:
                raise ValueError("retry")
            return x + y

        result = func(10, 20)
        assert result == 30
        assert all(args == (10, 20) for args in received_args)
