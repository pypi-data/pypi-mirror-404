# AutoParallel

Automatic parallel execution decorator for Python using joblib. Just add type hints and `@parallel` - that's it!

[![PyPI version](https://badge.fury.io/py/autoparallel.svg)](https://badge.fury.io/py/autoparallel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation
```bash
pip install autoparallel
```

## Quick Start
```python
from autoparallel import parallel
from pathlib import Path

@parallel
def process_file(filepath: Path, output_folder: str, prefix: str = "processed"):
    """
    filepath: Automatically parallelized (iterable parameter)
    output_folder: Stays constant across all parallel executions
    prefix: Stays constant across all parallel executions
    """
    content = filepath.read_text()
    output_path = Path(output_folder) / f"{prefix}_{filepath.name}"
    output_path.write_text(content.upper())
    return str(output_path)

# Automatically runs in parallel! 
# Only filepath changes, output_folder and prefix stay constant
results = process_file(
    Path(".").glob("*.txt"),
    output_folder="./processed",
    prefix="UPPER"
)
```

## How It Works

AutoParallel uses **type hints** to automatically detect which parameter should be parallelized:

1. ✅ Finds parameters with iterable type hints (`list`, `tuple`, etc.)
2. ✅ Parallelizes that parameter across all CPU cores
3. ✅ Keeps all other parameters constant
4. ✅ Returns results in the same order as input

**No manual configuration needed** - your type hints are the configuration!

## Examples

### Image Processing with Constants
```python
from autoparallel import parallel
from PIL import Image
from pathlib import Path

@parallel
def resize_images(
    image_file: Path,      # Parallelized - one task per image
    output_dir: str,       # Constant - same for all tasks
    width: int,            # Constant - same for all tasks
    height: int,           # Constant - same for all tasks
    quality: int = 85      # Constant - same for all tasks
) -> str:
    img = Image.open(image_file)
    img.thumbnail((width, height))
    output_path = Path(output_dir) / image_file.name
    img.save(output_path, quality=quality)
    return str(output_path)

# Process 100 images in parallel, all with same dimensions and quality
results = resize_images(
    Path("./photos").glob("*.jpg"),
    output_dir="./thumbnails",
    width=200,
    height=200,
    quality=90
)
```

### File Operations with Multiple Constants
```python
import shutil

@parallel
def backup_files(
    filepath: list[Path],    # Parallelized
    backup_dir: str,         # Constant
    prefix: str,             # Constant
    compress: bool = False   # Constant
) -> str:
    dest = Path(backup_dir) / f"{prefix}_{filepath.name}"
    if compress:
        shutil.make_archive(str(dest), 'zip', filepath.parent, filepath.name)
        return f"{dest}.zip"
    else:
        shutil.copy(filepath, dest)
        return str(dest)

files = list(Path("./important").glob("*.doc"))
backup_files(files, backup_dir="./backup", prefix="2024", compress=True)
```

### Data Processing
```python
import pandas as pd

@parallel
def process_csv(
    csv_file: Path,
    output_format: str,
    decimal_places: int = 2
) -> str:
    df = pd.read_csv(csv_file)
    df = df.round(decimal_places)
    
    output_file = csv_file.with_suffix(f'.{output_format}')
    
    if output_format == 'parquet':
        df.to_parquet(output_file)
    elif output_format == 'json':
        df.to_json(output_file)
    
    return str(output_file)

# Convert all CSVs to parquet in parallel
process_csv(
    Path("./data").glob("*.csv"),
    output_format="parquet",
    decimal_places=3
)
```

### Web Scraping with Threading
```python
import requests

@parallel(backend="threading", n_jobs=10)  # Use threading for I/O
def download_pages(
    url: list[str],
    output_dir: str,
    timeout: int = 30
) -> str:
    response = requests.get(url, timeout=timeout)
    filename = url.split("/")[-1] or "index.html"
    output_path = Path(output_dir) / filename
    output_path.write_bytes(response.content)
    return str(output_path)

urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

download_pages(urls, output_dir="./downloads", timeout=60)
```

## Works with Any Iterable
```python
@parallel
def compute(n: int) -> int:
    return n ** 2

# Lists
compute([1, 2, 3, 4])

# Ranges
compute(range(100))

# Generators
compute(x for x in range(10))

# Path.glob()
compute(Path(".").glob("*.txt"))

# Tuples
compute((5, 10, 15, 20))
```

## Configuration Options
```python
@parallel(
    n_jobs=4,              # Number of parallel jobs (-1 = all cores)
    backend="loky",        # Backend: 'loky', 'threading', 'multiprocessing'
    verbose=5              # Progress verbosity (0-10)
)
def process(items: list[str], constant: str) -> str:
    return f"{constant}: {items}"
```

### Backend Options

- **`loky`** (default): Best for CPU-bound tasks, safest option
- **`threading`**: Best for I/O-bound tasks (network, disk)
- **`multiprocessing`**: Alternative for CPU-bound tasks

### Verbosity Levels

- `0`: Silent (default)
- `1-10`: Show progress (higher = more detailed)

## Type Hints Required

AutoParallel **requires type hints** to work. If you forget them, you'll get a helpful error:
```python
@parallel
def process(items, folder):  # ❌ No type hints!
    ...

# Error: Function 'process' has no type hints.
# Please add type hints to indicate which parameter should be parallelized.
# Example:
#   @parallel
#   def process(items: list[str], folder: str):
#       ...
```

## Multiple Iterables

If your function has multiple iterable parameters, AutoParallel parallelizes the **last one**:
```python
@parallel
def process(
    metadata: list[dict],  # Not parallelized
    files: list[Path],     # Parallelized (last iterable)
    output: str            # Constant
):
    # files is split across workers
    # metadata and output stay constant
    ...
```

## Error Handling

AutoParallel provides clear, actionable error messages:
```python
from autoparallel import NoIterableParameterError

try:
    @parallel
    def bad_function(x, y):  # No type hints
        return x + y
    
    bad_function([1, 2], 3)
except NoIterableParameterError as e:
    print(e)
    # "Function 'bad_function' has no type hints..."
```

## Requirements

- Python 3.8+
- joblib >= 1.3.0

## Advanced Usage

### Custom Worker Count
```python
# Use 4 workers instead of all cores
@parallel(n_jobs=4)
def process(items: list[int]) -> int:
    return items * 2
```

### Progress Monitoring
```python
# Show detailed progress
@parallel(verbose=10)
def long_task(items: list[str]) -> str:
    # You'll see progress bar and timing info
    return items.upper()
```

### Mixing with Other Decorators
```python
from functools import lru_cache

@parallel
@lru_cache(maxsize=128)  # Cache results
def expensive_computation(n: int) -> int:
    return n ** 2
```

## Performance Tips

1. **Use `backend="threading"`** for I/O-bound tasks (network, file I/O)
2. **Use `backend="loky"`** (default) for CPU-bound tasks
3. **Set `n_jobs`** appropriately - more isn't always better
4. **Batch small tasks** - overhead of parallelization matters for tiny tasks

## Contributing

Contributions welcome! Please check out our [GitHub repository](https://github.com/kamballu/autoparallel).

## License

MIT License - see [LICENSE](LICENSE) file for details.

