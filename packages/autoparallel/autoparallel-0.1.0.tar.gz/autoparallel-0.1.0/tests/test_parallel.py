"""Test cases for the parallel decorator."""

from pathlib import Path
from typing import List

import pytest

from autoparallel import parallel


def test_parallel_with_list() -> None:
    """Test basic list parallelization."""

    @parallel
    def square(n: int) -> int:
        return n * n

    result = square([1, 2, 3, 4])
    assert result == [1, 4, 9, 16]


def test_parallel_with_type_hints() -> None:
    """Test with proper type hints."""

    @parallel
    def process(x: List[int]) -> int:
        return x * 2

    result = process([1, 2, 3])
    assert result == [2, 4, 6]


def test_parallel_with_range() -> None:
    """Test with range object."""

    @parallel
    def cube(n: int) -> int:
        return n**3

    result = cube(range(4))
    assert result == [0, 1, 8, 27]


def test_parallel_with_tuple() -> None:
    """Test with tuple input."""

    @parallel
    def double(x: int) -> int:
        return x * 2

    result = double((5, 10, 15))
    assert result == [10, 20, 30]


def test_parallel_single_item_fallback() -> None:
    """Test fallback to normal execution with single item."""

    @parallel
    def identity(x: int) -> int:
        return x

    result = identity(42)
    assert result == 42


def test_parallel_with_custom_params() -> None:
    """Test with custom n_jobs parameter."""

    @parallel(n_jobs=2, backend="loky")
    def add_one(n: int) -> int:
        return n + 1

    result = add_one([1, 2, 3])
    assert result == [2, 3, 4]


def test_parallel_empty_list() -> None:
    """Test with empty list falls back to normal execution."""

    @parallel
    def noop(x: List[int]) -> str:
        return "executed"

    result = noop([])
    assert result == "executed"


def test_parallel_with_generator() -> None:
    """Test with generator expression."""

    @parallel
    def times_three(n: int) -> int:
        return n * 3

    result = times_three(x for x in range(3))
    assert result == [0, 3, 6]


def test_parallel_preserves_function_metadata() -> None:
    """Test that decorator preserves function name and docstring."""

    @parallel
    def documented_function(x: int) -> int:
        """This is a docstring."""
        return x

    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This is a docstring."
