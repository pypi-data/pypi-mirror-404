"""Test cases for the parallel decorator."""

from pathlib import Path
from typing import List
import tempfile
import shutil

import pytest

from autoparallel import parallel, NoIterableParameterError


def test_parallel_with_list() -> None:
    """Test basic list parallelization."""

    @parallel
    def square(numbers: List[int]) -> int:  # numbers is List, but receives single int
        return numbers * numbers  # numbers is actually a single int here

    result = square([1, 2, 3, 4])
    assert result == [1, 4, 9, 16]


def test_parallel_with_type_hints() -> None:
    """Test with proper type hints."""

    @parallel
    def process(items: List[int]) -> int:  # items is List, receives single int
        return items * 2

    result = process([1, 2, 3])
    assert result == [2, 4, 6]


def test_parallel_with_range() -> None:
    """Test with range object."""

    @parallel
    def cube(numbers: List[int]) -> int:  # List type hint, receives single int
        return numbers**3

    result = cube(range(4))
    assert result == [0, 1, 8, 27]


def test_parallel_with_tuple() -> None:
    """Test with tuple input."""

    @parallel
    def double(items: List[int]) -> int:  # List type hint, receives single int
        return items * 2

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
    def add_one(numbers: List[int]) -> int:  # List type hint, receives single int
        return numbers + 1

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
    def times_three(numbers: List[int]) -> int:  # List type hint, receives single int
        return numbers * 3

    result = times_three(x for x in range(3))
    assert result == [0, 3, 6]


def test_parallel_preserves_function_metadata() -> None:
    """Test that decorator preserves function name and docstring."""

    @parallel
    def documented_function(items: List[int]) -> int:
        """This is a docstring."""
        return items

    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This is a docstring."


def test_parallel_with_constant_parameters() -> None:
    """Test that non-iterable parameters remain constant across parallel calls."""

    @parallel
    def multiply_and_add(items: List[int], multiplier: int, offset: int) -> int:
        return items * multiplier + offset

    result = multiply_and_add([1, 2, 3], multiplier=10, offset=5)
    assert result == [15, 25, 35]


def test_parallel_with_multiple_constants() -> None:
    """Test function with one iterable and multiple constant parameters."""

    @parallel
    def format_string(texts: List[str], prefix: str, suffix: str, uppercase: bool) -> str:
        result = f"{prefix}{texts}{suffix}"
        return result.upper() if uppercase else result

    texts_list = ["hello", "world", "test"]
    result = format_string(texts_list, prefix="[", suffix="]", uppercase=True)
    assert result == ["[HELLO]", "[WORLD]", "[TEST]"]


def test_parallel_with_path_objects() -> None:
    """Test with Path.glob() which returns a generator of Path objects."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        (tmp_path / "test1.txt").write_text("content1")
        (tmp_path / "test2.txt").write_text("content2")
        (tmp_path / "test3.txt").write_text("content3")
        
        @parallel
        def read_file(filepaths: List[Path]) -> str:  # List type hint, receives single Path
            return filepaths.read_text()
        
        results = read_file(tmp_path.glob("*.txt"))
        assert sorted(results) == ["content1", "content2", "content3"]


def test_parallel_file_copy_with_constant_destination() -> None:
    """Test real-world use case: copying files to a constant destination."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_dir = tmp_path / "source"
        dst_dir = tmp_path / "destination"
        src_dir.mkdir()
        dst_dir.mkdir()
        
        # Create source files
        files = []
        for i in range(3):
            file_path = src_dir / f"file{i}.txt"
            file_path.write_text(f"content{i}")
            files.append(file_path)
        
        @parallel
        def copy_file(filepaths: List[Path], destination: str) -> str:
            dest_path = Path(destination) / filepaths.name
            shutil.copy(filepaths, dest_path)
            return str(dest_path)
        
        results = copy_file(files, destination=str(dst_dir))
        
        # Verify all files were copied
        assert len(results) == 3
        for i in range(3):
            assert (dst_dir / f"file{i}.txt").exists()
            assert (dst_dir / f"file{i}.txt").read_text() == f"content{i}"


def test_no_type_hints_raises_error() -> None:
    """Test that missing type hints raises a clear error."""
    
    @parallel
    def no_hints(items, constant):
        return items + constant
    
    with pytest.raises(NoIterableParameterError) as exc_info:
        no_hints([1, 2, 3], 10)
    
    assert "no type hints" in str(exc_info.value).lower()
    assert "no_hints" in str(exc_info.value)


def test_partial_type_hints_raises_error() -> None:
    """Test that having untyped iterable parameters raises helpful error."""
    
    @parallel
    def partial_hints(items, constant: int):  # items has no type hint
        return items + constant
    
    with pytest.raises(NoIterableParameterError) as exc_info:
        partial_hints([1, 2, 3], 10)
    
    error_msg = str(exc_info.value).lower()
    assert "type hints" in error_msg


def test_multiple_iterables_uses_last() -> None:
    """Test that when multiple iterables exist, the last one is parallelized."""
    
    @parallel
    def process_with_multiple_lists(
        prefixes: List[str],
        items: List[int],
        suffix: str
    ) -> str:
        # items should be parallelized, prefixes should be constant
        return f"{prefixes[0]}-{items}-{suffix}"
    
    result = process_with_multiple_lists(
        prefixes=["A", "B"],
        items=[1, 2, 3],
        suffix="end"
    )
    
    assert result == ["A-1-end", "A-2-end", "A-3-end"]


def test_parallel_with_default_arguments() -> None:
    """Test that default arguments work correctly."""
    
    @parallel
    def with_defaults(items: List[int], multiplier: int = 2, offset: int = 0) -> int:
        return items * multiplier + offset
    
    # Without defaults
    result1 = with_defaults([1, 2, 3])
    assert result1 == [2, 4, 6]
    
    # With custom values
    result2 = with_defaults([1, 2, 3], multiplier=3, offset=10)
    assert result2 == [13, 16, 19]


def test_parallel_with_kwargs() -> None:
    """Test that kwargs work correctly."""
    
    @parallel
    def process_kwargs(data: List[str], prefix: str, suffix: str) -> str:
        return f"{prefix}{data}{suffix}"
    
    result = process_kwargs(
        data=["a", "b", "c"],
        prefix="<",
        suffix=">"
    )
    assert result == ["<a>", "<b>", "<c>"]


def test_parallel_no_iterables_runs_normally() -> None:
    """Test that functions with no iterables run normally without error."""
    
    @parallel
    def no_iterables(x: int, y: int) -> int:
        return x + y
    
    result = no_iterables(5, 10)
    assert result == 15


def test_parallel_with_complex_types() -> None:
    """Test with more complex type hints."""
    
    from typing import Tuple
    
    @parallel
    def process_tuples(items: List[Tuple[int, str]], separator: str) -> str:
        return f"{items[0]}{separator}{items[1]}"
    
    data = [(1, "a"), (2, "b"), (3, "c")]
    result = process_tuples(data, separator="-")
    assert result == ["1-a", "2-b", "3-c"]


def test_parallel_backend_threading() -> None:
    """Test that threading backend works for I/O bound tasks."""
    
    @parallel(backend="threading", n_jobs=2)
    def io_task(items: List[int]) -> int:
        import time
        time.sleep(0.01)
        return items * 2
    
    result = io_task([1, 2, 3, 4])
    assert result == [2, 4, 6, 8]


def test_parallel_preserves_order() -> None:
    """Test that results maintain the same order as input."""
    
    @parallel
    def identity(items: List[int]) -> int:
        import time
        # Add random delay to test order preservation
        time.sleep(0.001 * (10 - items))
        return items
    
    input_data = list(range(10))
    result = identity(input_data)
    assert result == input_data


def test_real_world_image_resize() -> None:
    """Test realistic image processing scenario."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create dummy "image" files
        files = []
        for i in range(5):
            file_path = tmp_path / f"image{i}.txt"
            file_path.write_text(f"image_data_{i}")
            files.append(file_path)
        
        @parallel
        def process_image(
            image_files: List[Path],
            output_folder: str,
            prefix: str,
            quality: int
        ) -> str:
            # Simulate image processing
            content = image_files.read_text()
            processed = f"processed_{quality}_{content}"
            
            output_path = Path(output_folder) / f"{prefix}_{image_files.name}"
            output_path.write_text(processed)
            return str(output_path)
        
        results = process_image(
            files,
            output_folder=str(output_dir),
            prefix="thumb",
            quality=85
        )
        
        assert len(results) == 5
        for i in range(5):
            output_file = output_dir / f"thumb_image{i}.txt"
            assert output_file.exists()
            content = output_file.read_text()
            assert "processed_85_image_data_" in content


def test_parallel_with_none_values() -> None:
    """Test handling of None values in results."""
    
    @parallel
    def maybe_process(items: List[int]) -> int | None:
        return items if items > 0 else None
    
    result = maybe_process([-1, 0, 1, 2, -5])
    assert result == [None, None, 1, 2, None]