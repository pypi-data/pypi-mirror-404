# AutoParallel

Automatic parallel execution decorator for Python using a thin wrapper around joblib.

## Installation
```bash
pip install autoparallel
```

## Usage

Just add `@parallel` to any function and it automatically parallelizes when you pass iterables:
```python
from autoparallel import parallel
from pathlib import Path

@parallel
def process_file(filepath):
    content = Path(filepath).read_text()
    return content.upper()

# Automatically runs in parallel!
results = process_file(["file1.txt", "file2.txt", "file3.txt"])
```

### Works with any iterable
```python
@parallel
def compute(n: int) -> int:
    return n ** 2

# Works with lists
compute([1, 2, 3, 4])

# Works with ranges
compute(range(100))

# Works with generators
compute(x for x in range(10))

# Works with Path.glob()
compute(Path(".").glob("*.txt"))
```

### Customize parallelization
```python
@parallel(n_jobs=4, backend="threading", verbose=5)
def download(url: str) -> bytes:
    import requests
    return requests.get(url).content

urls = ["http://example.com/1", "http://example.com/2"]
data = download(urls)
```

### Parameters

- `n_jobs`: Number of parallel jobs (`-1` = all CPU cores, default: `-1`)
- `backend`: Joblib backend (`'loky'`, `'threading'`, `'multiprocessing'`, default: `'loky'`)
- `verbose`: Progress verbosity (`0-10`, default: `0`)

## How it works

1. Detects the first iterable parameter (using type hints or duck typing)
2. Splits the iterable into individual items
3. Runs your function in parallel for each item using joblib
4. Returns a list of results

If no iterable is found, the function runs normally (no parallelization).

## Requirements

- Python 3.8+
- joblib >= 1.3.0

## License

MIT
