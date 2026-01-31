# Quick-Logger-Colorful
A lightweight Python logging tool with **colorful terminal output**(Otherwise, why would it be called Colorful?), **automatic exception capture**, **sync/async support**. Designed for fast integration in Python projects, supporting log grading and date-based log file splitting.

[![PyPI Version](https://img.shields.io/pypi/v/quick-logger-colorful.svg)](https://pypi.org/project/quick-logger-colorful/)
[![Python Versions](https://img.shields.io/pypi/pyversions/quick-logger-colorful.svg)](https://pypi.org/project/quick-logger-colorful/)
[![License](https://img.shields.io/pypi/l/quick-logger-colorful.svg)](https://github.com/huyuenshen/quick-logger/blob/main/LICENSE)

## Features
- **Log Grading**: Supports 5 levels - DEBUG(0), INFO(1), WARN(2), ERROR(3), FATAL(4)
- **Colorful Output**: Distinct colors for better visibility:
  - DEBUG: Cyan
  - INFO: Green
  - WARN: Yellow
  - ERROR: Red
  - FATAL: Red background + White text
- **Auto Exception Capture**: One-line decorator for both sync/async functions, with fatal exception marking
- **Zero Configuration**: Automatically creates log directories and configuration files on first run
- **Date-based Splitting**: Generates separate log files for each day to avoid oversized files
- **Dual Mode Support**: Sync logging (core module) + Async logging (asynclog module)
- **Mode Switch**: Toggle debug/production mode with `-O` command-line argument

## Installation
### PyPI Installation (Recommended)
```bash
pip install quick-logger-colorful
```

### Local Installation
1. Clone the repository:
```bash
git clone https://github.com/huyuenshen/quick-logger.git
cd quick-logger
```
2. Install from source:
```bash
pip install .
```

## Quick Start
### 1. Sync Logging (Core Module)
```python
from quick_logger import Logger, start_logger

# Initialize logger
logger = Logger()

# Log messages of different levels
logger.log("This is a DEBUG message", typ=0)
logger.log("This is an INFO message", typ=1)
logger.log("This is a WARN message", typ=2)
logger.log("This is an ERROR message", typ=3)
logger.log("This is a FATAL message", typ=4)  # New FATAL level

# Exception capture with decorator (mark specific exceptions as FATAL)
@start_logger
def test_function():
    logger.log("Running sync test function", typ=1)
    raise KeyError("Critical error (marked as FATAL)")  # Triggers FATAL log

if __name__ == "__main__":
    try:
        test_function()
    except Exception:
        pass
```

### 2. Async Logging (asynclog Module)
For asynchronous functions, use the `asynclog` module to avoid blocking the event loop:
```python
import asyncio
from quick_logger import asynclog

async def async_test_func():
    logger = asynclog.Logger()
    await logger.log("This is an async INFO message", typ=1)
    await logger.log("This is an async FATAL message", typ=4)  # Async FATAL log
    await asyncio.sleep(1)  # Simulate async work (non-blocking)

# Async decorator with fatal exception marking
@asynclog.start_logger
async def wrapped_async_func():
    await async_test_func()
    raise KeyError("Async fatal error")  # Triggers FATAL log

if __name__ == "__main__":
    asyncio.run(wrapped_async_func())
```

### Mode Switch
- **Debug Mode (Default)**: Shows all log levels (DEBUG/INFO/WARN/ERROR/FATAL)
  ```bash
  python your_script.py
  ```
- **Production Mode**: Hides DEBUG level (shows INFO/WARN/ERROR/FATAL)
  ```bash
  python your_script.py -O
  ```

## Configuration
### Auto-generated Config File
On first run, a configuration file is created at `./Logger/.config/Config.json` with the following default content:
```json
{
    "pattern": "[{time}][{func}][{level}]:{msg}",
    "file": "./Logger/{date}.log.txt"
    "enable_color": true
}
```

- **pattern**: Log format template (supports `{time}`, `{func}`, `{level}`, `{msg}`)
- **file**: Log file path (`{date}` is replaced with the current date, e.g., `2025-12-25.log.txt`)
- **enable_color**: Log in console with color or not

### Custom Log Format
Modify the `pattern` field to customize the log format, e.g.:
```json
{
    "pattern": "[{time}] [{level}] [{func}] - {msg}"
}
```

## Compatibility
- **Python Versions**: 3.7+
- **Platforms**: Windows, macOS, Linux, Android (Python compilers like Pydroid)

## FAQ (Frequently Asked Questions)
### 1. Why is the FATAL log not printed to the file/terminal?
- Ensure the log level parameter `typ=4` is correctly passed (FATAL corresponds to 4, not other values);
- Check if the production mode (`-O` parameter) is accidentally enabled (production mode only hides DEBUG, not FATAL);
- Verify the write permission of the `./Logger/` directory (the library will not throw permission exceptions actively, please ensure the running user has read/write access).

### 2. How to disable colorful terminal output?
Colorful output is enabled by default. To disable it (e.g., for non-interactive terminals):
1. Create a `./Logger/.config/Config.json` file manually (if not generated);
2. Add the `"color": false` field to the configuration:
   ```json
   {
       "pattern": "[{time}][{func}][{level}]:{msg}",
       "file": "./Logger/{date}.log.txt",
       "enable_color": false
   }
   ```
3. Restart your script (the configuration takes effect on logger initialization).

### 3. Why does async logging block the event loop?
- Do NOT use `quick_logger.Logger` (sync version) in async functions — always use `quick_logger.asynclog.Logger`;
- Ensure all log calls in async functions are prefixed with `await` (e.g., `await logger.log(...)`), missing `await` will cause synchronous blocking.

### 4. How to customize the log date format?
The `{date}` placeholder in the `file` field uses the format `YYYY-MM-DD` by default. To modify it:
1. Modify the `file` field in `Config.json` (supports Python `strftime` format):
   ```json
   {
       "file": "./Logger/{date:%Y%m%d}.log.txt"  // Outputs: 20251225.log.txt
   }
   ```
2. The `{time}` placeholder in `pattern` uses `HH:MM:SS` by default, to customize:
   Modify the logger initialization (add `time_format` parameter):
   ```python
   from quick_logger import Logger
   logger = Logger(time_format="%Y-%m-%d %H:%M:%S.%f")  // Includes milliseconds
   ```

### 5. Can I use this library with Django/FastAPI/Flask?
- **FastAPI (Async)**: Use `asynclog.Logger` in route functions (add `await` for log calls), and apply `@asynclog.start_logger` to async route handlers;
- **Django/Flask (Sync)**: Use the core `Logger` class directly, apply `@start_logger` to view functions (ensure the logger is initialized once, e.g., in `settings.py`);
- Avoid initializing `Logger` repeatedly (recommended to use a singleton instance).

### 6. How to change the default log directory (./Logger/)?
Modify the `file` field in `Config.json` to specify a custom path:
```json
{
    "file": "/var/log/my_project/{date}.log.txt"  // Absolute path (Linux/macOS)
    // "file": "D:\\Logs\\my_project\\{date}.log.txt"  // Absolute path (Windows)
}
```
The log directory will be created automatically (ensure the running user has permission to write to the target path).

### 7. Why are some function names missing in the {func} placeholder?
- For decorated functions: The `{func}` placeholder shows the wrapped function name by default. To display the original function name, modify the decorator to preserve metadata:
  ```python
  # In start_logger decorator implementation
  import functools
  def start_logger(func):
      @functools.wraps(func)  # Add this line to preserve func name
      def wrapper(*args, **kwargs):
          # Original decorator logic
          pass
      return wrapper
  ```
- For anonymous functions (lambda): `{func}` will show `<lambda>` (this is expected behavior).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Issues and pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.