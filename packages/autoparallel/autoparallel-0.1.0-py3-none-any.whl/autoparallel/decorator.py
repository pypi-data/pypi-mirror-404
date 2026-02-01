"""Core parallel decorator implementation."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any, TypeVar, get_origin, get_type_hints

from joblib import Parallel, delayed

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def parallel(
    func: F | None = None,
    *,
    n_jobs: int = -1,
    backend: str = "loky",
    verbose: int = 0,
) -> F | Callable[[F], F]:
    """
    Automatically parallelize function calls on iterable arguments using joblib.

    Detects the first iterable parameter (list, tuple, generator, Path.glob, etc.)
    and executes the function in parallel for each item.

    Args:
        func: Function to decorate (automatically passed when used without parentheses)
        n_jobs: Number of parallel jobs. -1 uses all CPU cores. Default: -1
        backend: Joblib backend ('loky', 'threading', 'multiprocessing'). Default: 'loky'
        verbose: Verbosity level for joblib (0-10). Higher shows progress. Default: 0

    Returns:
        Decorated function that executes in parallel when given iterables

    Examples:
        Simple usage with all defaults:
        >>> @parallel
        ... def process_file(filepath: str) -> str:
        ...     return Path(filepath).read_text().upper()
        >>> results = process_file(["a.txt", "b.txt"])

        With custom parameters:
        >>> @parallel(n_jobs=4, backend="threading", verbose=5)
        ... def download(url: str) -> bytes:
        ...     return requests.get(url).content
        >>> data = download(url_list)

        Works with any iterable:
        >>> @parallel
        ... def compute(n: int) -> int:
        ...     return n ** 2
        >>> results = compute(range(100))
        >>> results = compute(Path(".").glob("*.txt"))
    """

    def decorator(f: F) -> F:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature and type hints
            sig = inspect.signature(f)
            try:
                hints = get_type_hints(f)
            except Exception:
                hints = {}

            # Bind arguments to parameter names
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Find first iterable parameter
            iterable_param: str | None = None
            iterable_data: list[Any] | None = None

            for param_name, param_value in bound.arguments.items():
                # Check type hints first
                if param_name in hints:
                    origin = get_origin(hints[param_name])
                    if origin in (list, tuple):
                        try:
                            iterable_data = list(param_value)
                            iterable_param = param_name
                            break
                        except (TypeError, ValueError):
                            pass

                # Duck typing fallback for common iterables
                if isinstance(param_value, (list, tuple)):
                    iterable_data = list(param_value)
                    iterable_param = param_name
                    break
                elif hasattr(param_value, "__iter__") and not isinstance(
                    param_value, (str, bytes, dict)
                ):
                    try:
                        iterable_data = list(param_value)
                        if iterable_data:  # Only use if not empty
                            iterable_param = param_name
                            break
                    except (TypeError, ValueError):
                        pass

            # No iterable found or empty - run normally
            if iterable_param is None or not iterable_data:
                return f(*args, **kwargs)

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
