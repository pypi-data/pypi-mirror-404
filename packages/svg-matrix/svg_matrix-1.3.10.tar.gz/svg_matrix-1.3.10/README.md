# svg-matrix (Python)

Python wrapper for [svg-matrix](https://github.com/Emasoft/SVG-MATRIX) - arbitrary-precision SVG optimization, validation, and manipulation.

## Installation

### As a CLI Tool (Recommended)

For command-line usage, install as a [uv](https://docs.astral.sh/uv/) tool:

```bash
uv tool install svg-matrix --python 3.12
```

This installs `psvgm`, `psvg-matrix`, `psvgfonts`, and `psvglinter` globally.

**Upgrade to latest version:**

```bash
uv tool upgrade svg-matrix
```

**Uninstall:**

```bash
uv tool uninstall svg-matrix
```

**List installed tools:**

```bash
uv tool list
```

### As a Library

For use in Python projects:

```bash
pip install svg-matrix
# or
uv add svg-matrix
```

**Prerequisites:** Requires [Bun](https://bun.sh/) (recommended) or [Node.js](https://nodejs.org/) installed on your system. The package will attempt to auto-install Bun if neither is found.

```bash
# Install Bun (recommended, faster)
curl -fsSL https://bun.sh/install | bash

# Or use Node.js
# https://nodejs.org/
```

## Quick Start

```python
from svg_matrix import validate_svg, optimize_svg, to_plain_svg

# Validate an SVG file
result = validate_svg("icon.svg")
if result["valid"]:
    print("SVG is valid!")
else:
    for issue in result["issues"]:
        print(f"Issue: {issue['reason']}")

# Optimize an SVG file
optimize_svg("large.svg", "small.svg", precision=4)

# Convert Inkscape SVG to plain SVG
to_plain_svg("inkscape_drawing.svg", "plain.svg")
```

## Features

### Validation

```python
from svg_matrix import validate_svg, validate_svg_async

# Synchronous validation
result = validate_svg("file.svg")
# Returns: {"valid": bool, "issues": list, "error": str|None}

# Async validation
import asyncio
result = await validate_svg_async("file.svg")

# Validate SVG string content
result = validate_svg('<svg xmlns="http://www.w3.org/2000/svg">...</svg>')
```

### Optimization

```python
from svg_matrix import optimize_svg, optimize_paths

# Full optimization
optimize_svg("input.svg", "output.svg",
    precision=6,        # Decimal precision (default: 6)
    minify=True,        # Minify output
    remove_comments=True,
    remove_metadata=True
)

# Path-only optimization (lighter)
optimize_paths("input.svg", "output.svg", precision=4)
```

### Conversion

```python
from svg_matrix import to_plain_svg, flatten, convert_shapes

# Remove Inkscape namespaces
to_plain_svg("inkscape.svg", "plain.svg")

# Flatten transforms, groups, clipPaths
flatten("complex.svg", "flat.svg",
    flatten_transforms=True,
    flatten_groups=True,
    flatten_clipaths=True
)

# Convert shapes to paths
convert_shapes("shapes.svg", "paths.svg")
```

### Direct CLI Access

```python
from svg_matrix import run_svgm, run_svg_matrix, get_info

# Run svgm with any arguments
result = run_svgm(["input.svg", "-o", "output.svg", "-p", "4"])
print(result["stdout"])

# Run svg-matrix commands
result = run_svg_matrix(["info", "file.svg"])

# Get SVG info
info = get_info("file.svg")
print(f"Width: {info.get('width')}, Height: {info.get('height')}")
```

## CLI Commands

The package installs CLI wrappers that mirror the Node.js/Bun commands exactly:

| Python CLI | Mirrors | Description |
|------------|---------|-------------|
| `psvgm` | `svgm` | SVG optimization |
| `psvg-matrix` | `svg-matrix` | SVG matrix operations |
| `psvgfonts` | `svgfonts` | SVG font operations |
| `psvglinter` | `svglinter` | SVG linting |

```bash
# Optimize SVG (same options as svgm)
psvgm input.svg -o output.svg -p 4

# Get SVG info
psvg-matrix info input.svg

# Lint SVG
psvglinter input.svg

# Font operations
psvgfonts embed input.svg -o output.svg

# Show help (same as Node.js version)
psvgm --help
psvg-matrix --help
```

## Batch Processing

```python
from pathlib import Path
from svg_matrix import validate_svg, optimize_svg

# Process all SVGs in a directory
svg_dir = Path("./svgs")
output_dir = Path("./optimized")
output_dir.mkdir(exist_ok=True)

for svg_file in svg_dir.glob("*.svg"):
    result = validate_svg(svg_file)
    if result["valid"]:
        optimize_svg(svg_file, output_dir / svg_file.name)
        print(f"Optimized: {svg_file.name}")
    else:
        print(f"Skipped (invalid): {svg_file.name}")
```

## API Reference

### Validation Functions

| Function | Description |
|----------|-------------|
| `validate_svg(svg_input, strict=False)` | Validate SVG file or string |
| `validate_svg_async(svg_input, strict=False)` | Async validation |

### Optimization Functions

| Function | Description |
|----------|-------------|
| `optimize_svg(input, output, ...)` | Full SVG optimization |
| `optimize_paths(input, output, precision)` | Path-only optimization |

### Conversion Functions

| Function | Description |
|----------|-------------|
| `to_plain_svg(input, output)` | Remove Inkscape namespaces |
| `flatten(input, output, ...)` | Flatten transforms/groups |
| `convert_shapes(input, output)` | Convert shapes to paths |

### CLI Functions

| Function | Description |
|----------|-------------|
| `run_svgm(args, timeout)` | Run svgm CLI |
| `run_svg_matrix(args, timeout)` | Run svg-matrix CLI |
| `get_info(svg_path)` | Get SVG file info |

## How It Works

This package is a thin Python wrapper around the [@emasoft/svg-matrix](https://www.npmjs.com/package/@emasoft/svg-matrix) npm package. It uses `bunx` (or `npx` as fallback) to execute the Node.js CLI tools.

**Advantages:**
- Always uses the latest svg-matrix version
- Minimal Python package size (~20KB)
- Full feature parity with the Node.js library

**Requirements:**
- Bun or Node.js must be installed
- First run may take a few seconds to download the npm package

## License

MIT License - see [LICENSE](LICENSE)

## Links

- [GitHub Repository](https://github.com/Emasoft/SVG-MATRIX)
- [npm Package](https://www.npmjs.com/package/@emasoft/svg-matrix)
- [Issue Tracker](https://github.com/Emasoft/SVG-MATRIX/issues)
