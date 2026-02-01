"""Core parallel decorator implementation."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, get_origin, get_type_hints

from joblib import Parallel, delayed

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class NoIterableParameterError(Exception):
    """Raised when no iterable parameter can be detected."""
    pass


def parallel(
    func: F | None = None,
    *,
    n_jobs: int = -1,
    backend: str = "loky",
    verbose: int = 0,
) -> F | Callable[[F], F]:
    """
    Automatically parallelize function calls on iterable arguments using joblib.

    Uses type hints to intelligently detect which parameter should be parallelized.
    All other parameters remain constant across parallel executions.

    Args:
        func: Function to decorate (automatically passed when used without parentheses)
        n_jobs: Number of parallel jobs. -1 uses all CPU cores. Default: -1
        backend: Joblib backend ('loky', 'threading', 'multiprocessing'). Default: 'loky'
        verbose: Verbosity level for joblib (0-10). Higher shows progress. Default: 0

    Returns:
        Decorated function that executes in parallel when given iterables

    Raises:
        NoIterableParameterError: When no iterable parameter can be detected from type hints

    Examples:
        Basic usage with type hints:
        >>> @parallel
        ... def process_image(image_path: Path, output_folder: str, quality: int = 95):
        ...     # output_folder and quality stay constant
        ...     # image_path is automatically parallelized
        ...     img = Image.open(image_path)
        ...     img.save(Path(output_folder) / image_path.name, quality=quality)
        >>> 
        >>> process_image(Path(".").glob("*.jpg"), "./output", quality=85)

        Multiple constants:
        >>> @parallel
        ... def copy_files(filepath: list[Path], dest: str, prefix: str):
        ...     shutil.copy(filepath, Path(dest) / f"{prefix}_{filepath.name}")
        >>> 
        >>> copy_files(list(Path(".").glob("*.txt")), "./backup", "backup")
    """

    def decorator(f: F) -> F:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature and type hints
            sig = inspect.signature(f)
            
            # Try to get type hints - if fails, raise explicit error
            try:
                hints = get_type_hints(f)
            except Exception:
                hints = {}
            
            if not hints:
                raise NoIterableParameterError(
                    f"Function '{f.__name__}' has no type hints. "
                    f"Please add type hints to indicate which parameter should be parallelized.\n"
                    f"Example:\n"
                    f"  @parallel\n"
                    f"  def {f.__name__}(items: list[str], constant_param: str):\n"
                    f"      ..."
                )

            # Bind arguments to parameter names
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Find all iterable parameters from type hints
            iterable_candidates: list[tuple[str, Any]] = []
            
            for param_name, param_value in bound.arguments.items():
                if param_name not in hints:
                    continue
                    
                origin = get_origin(hints[param_name])
                
                # Check if type hint indicates an iterable (list, tuple, etc.)
                if origin in (list, tuple):
                    try:
                        # Verify the actual value is iterable
                        iterable_data = list(param_value)
                        if iterable_data:  # Only consider non-empty iterables
                            iterable_candidates.append((param_name, iterable_data))
                    except (TypeError, ValueError):
                        # Type hint says iterable but value isn't - skip
                        pass
            
            # No iterable parameters found
            if not iterable_candidates:
                # Check if there are any actual iterables without type hints
                has_untyped_iterable = False
                for param_name, param_value in bound.arguments.items():
                    if param_name not in hints:
                        if hasattr(param_value, "__iter__") and not isinstance(
                            param_value, (str, bytes, dict)
                        ):
                            has_untyped_iterable = True
                            break
                
                if has_untyped_iterable:
                    raise NoIterableParameterError(
                        f"Found iterable parameter in '{f.__name__}' but it lacks type hints. "
                        f"Please add type hints to all parameters.\n"
                        f"Example:\n"
                        f"  @parallel\n"
                        f"  def {f.__name__}(..., items: list[YourType], ...):\n"
                        f"      ..."
                    )
                else:
                    # No iterables at all - run normally
                    return f(*args, **kwargs)
            
            # Use the last iterable parameter (most likely to be the "data")
            # Rationale: func(constant1, constant2, data_list) is more common than
            #            func(data_list, constant1, constant2)
            iterable_param, iterable_data = iterable_candidates[-1]
            
            # If multiple iterables, inform user (optional warning)
            if len(iterable_candidates) > 1 and verbose > 0:
                print(
                    f"Warning: Multiple iterable parameters found in '{f.__name__}': "
                    f"{[name for name, _ in iterable_candidates]}. "
                    f"Parallelizing '{iterable_param}' (last iterable parameter)."
                )

            # Build delayed tasks for joblib
            def make_task(item: Any) -> Any:
                task_kwargs = bound.arguments.copy()
                task_kwargs[iterable_param] = item
                return delayed(f)(**task_kwargs)

            # Execute in parallel
            tasks = [make_task(item) for item in iterable_data]
            results = Parallel(n_jobs=n_jobs, backend=backend, verbose=verbose)(tasks)

            return results

        return wrapper  # type: ignore[return-value]

    # Allow both @parallel and @parallel(...) syntax
    if func is not None:
        return decorator(func)

    return decorator