"""AutoParallel - Automatic parallel execution decorator."""

from autoparallel.decorator import parallel, NoIterableParameterError

__version__ = "0.2.0"
__all__ = ["parallel", "NoIterableParameterError"]