# sweepy

Sweep away unused imports from your codebase.

A minimal, zero-dependency Python tool that detects unused imports. Just point it at any local directory or GitHub URL.

## Installation

```bash
pip install sweepy-cli
```

## Usage

```bash
# Local directory
sweepy .
sweepy /path/to/repo

# GitHub URL (no clone needed)
sweepy https://github.com/user/repo

# Specific branch
sweepy https://github.com/user/repo/tree/develop
sweepy https://github.com/user/repo/tree/feature/new-api
```

### Options

```bash
# Exclude directories
sweepy . --exclude-dir migrations --exclude-dir tests

# Exclude files
sweepy . --exclude-file conftest.py
```

### Python API

```python
from sweepy import analyze

result = analyze("https://github.com/user/repo")

print(result.summary())

for item in result.unused_imports:
    print(f"{item.file}:{item.line} - {item.module}")
```

## Example Output

```
============================================================
SWEEPY ANALYSIS REPORT
============================================================
Repository: https://github.com/user/repo
Files analyzed: 42
Files skipped: 3
Unused imports: 5

------------------------------------------------------------

src/utils.py
   Line   3: json
   Line   7: typing

src/main.py
   Line   1: os
   Line   4: sys
   Line   5: re
```

## Why sweepy?

| | sweepy | ruff | autoflake |
|---|--------|------|-----------|
| Zero dependencies | O | O | X |
| GitHub URL support | O | X | X |
| Single purpose | O | X | X |
| Setup required | None | Config | Config |

sweepy does one thing: find unused imports. No config files, no complex rules, no setup.

## License

MIT