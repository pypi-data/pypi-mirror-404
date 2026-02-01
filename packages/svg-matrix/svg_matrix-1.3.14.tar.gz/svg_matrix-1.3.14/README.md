# svg-matrix (Python)

Python wrapper for [svg-matrix](https://github.com/Emasoft/SVG-MATRIX) — a powerful toolkit for SVG optimization, validation, font embedding, and matrix transformations with arbitrary precision.

## What This Package Does

This package provides Python access to the full svg-matrix toolkit:

| Tool | Purpose | Use Case |
|------|---------|----------|
| **psvgm** | SVG optimization | Reduce file size, clean up code, minify |
| **psvg-matrix** | Matrix operations | Flatten transforms, convert shapes, analyze |
| **psvgfonts** | Font management | Embed Google Fonts, extract fonts, subset |
| **psvglinter** | SVG linting | Validate syntax, find issues, auto-fix |

All commands are prefixed with `p` to avoid conflicts with the JavaScript versions.

## Installation

### Option 1: As a CLI Tool (Recommended)

Install globally using [uv](https://docs.astral.sh/uv/) for command-line access:

```bash
# Install the tool globally
uv tool install svg-matrix --python 3.12

# Verify installation
psvgm --version
psvgfonts --version
```

**Manage your installation:**

```bash
uv tool upgrade svg-matrix   # Upgrade to latest version
uv tool uninstall svg-matrix # Remove the tool
uv tool list                 # Show all installed tools
```

### Option 2: As a Python Library

For use in Python scripts and projects:

```bash
pip install svg-matrix
# or with uv:
uv add svg-matrix
```

### Prerequisites

Requires [Bun](https://bun.sh/) (recommended) or [Node.js](https://nodejs.org/):

```bash
# Install Bun (faster, recommended)
curl -fsSL https://bun.sh/install | bash

# Or use Node.js from https://nodejs.org/
```

The package will attempt to auto-install Bun if neither runtime is found.

---

## Quick Start

### Command Line

```bash
# Optimize an SVG (reduce size, clean up)
psvgm input.svg -o output.svg

# Embed Google Fonts into SVG for offline use
psvgfonts embed --woff2 input.svg -o output.svg

# Validate and auto-fix SVG issues
psvglinter --fix input.svg

# Get SVG information (dimensions, elements, fonts)
psvg-matrix info input.svg

# Show all options for any command
psvgm --help
psvgfonts --help
```

### Python API

```python
from svg_matrix import validate_svg, optimize_svg, run_svgfonts

# Validate an SVG file
result = validate_svg("icon.svg")
if result["valid"]:
    print("✓ SVG is valid!")
else:
    for issue in result["issues"]:
        print(f"✗ {issue['reason']}")

# Optimize an SVG (reduce file size)
optimize_svg("large.svg", "small.svg", precision=4)

# Embed fonts for offline use
result = run_svgfonts(["embed", "--woff2", "-o", "output.svg", "input.svg"])
```

---

## CLI Commands Reference

### psvgm — SVG Optimization

Optimize SVG files: reduce size, clean up code, remove unnecessary elements.

```bash
# Basic optimization
psvgm input.svg -o output.svg

# Set decimal precision (fewer decimals = smaller file)
psvgm input.svg -o output.svg -p 4

# Pretty print (human-readable output)
psvgm input.svg -o output.svg --pretty --indent 2

# Process entire directory recursively
psvgm ./icons/ -f ./optimized/ -r

# Show available plugins
psvgm --show-plugins

# Quiet mode (no output except errors)
psvgm input.svg -o output.svg -q
```

### psvgfonts — Font Management

Embed, extract, and manage fonts in SVG files.

```bash
# List fonts used in an SVG
psvgfonts list input.svg

# Embed fonts (downloads from Google Fonts, etc.)
psvgfonts embed input.svg -o output.svg

# Embed with WOFF2 compression (30% smaller)
psvgfonts embed --woff2 input.svg -o output.svg

# Embed only glyphs actually used (smallest size)
psvgfonts embed --woff2 --subset input.svg -o output.svg

# Extract embedded fonts to files
psvgfonts extract --extract-dir ./fonts/ input.svg

# Search for fonts by name
psvgfonts search --query "roboto" --limit 10

# Show font cache statistics
psvgfonts cache

# Clean old cached fonts
psvgfonts cache --cache-action clean --max-age 30
```

### psvg-matrix — Matrix Operations

Flatten transforms, convert shapes, and analyze SVG structure.

```bash
# Get SVG information
psvg-matrix info input.svg

# Flatten all transforms into paths
psvg-matrix flatten input.svg -o output.svg

# Convert shapes (rect, circle, etc.) to paths
psvg-matrix convert input.svg -o output.svg

# Remove Inkscape-specific data
psvg-matrix to-plain input.svg -o output.svg

# Normalize coordinates
psvg-matrix normalize input.svg -o output.svg
```

### psvglinter — SVG Validation

Validate SVG files and auto-fix common issues.

```bash
# Check for issues
psvglinter input.svg

# Auto-fix fixable issues
psvglinter --fix input.svg

# Show only errors (no warnings)
psvglinter --errors-only input.svg

# Process directory
psvglinter ./icons/
```

---

## Python API

### Validation

Check SVG files for issues before processing:

```python
from svg_matrix import validate_svg, validate_svg_async

# Validate a file
result = validate_svg("file.svg")
print(f"Valid: {result['valid']}")
print(f"Issues: {result['issues']}")

# Validate SVG string content
svg_content = '<svg xmlns="http://www.w3.org/2000/svg">...</svg>'
result = validate_svg(svg_content)

# Async validation (for batch processing)
import asyncio
result = await validate_svg_async("file.svg")
```

### Optimization

Reduce SVG file size while preserving visual appearance:

```python
from svg_matrix import optimize_svg, optimize_paths

# Full optimization with options
optimize_svg(
    "input.svg",
    "output.svg",
    precision=6,           # Decimal precision (default: 6)
    minify=True,           # Remove whitespace
    remove_comments=True,  # Remove XML comments
    remove_metadata=True   # Remove editor metadata
)

# Path-only optimization (faster, less aggressive)
optimize_paths("input.svg", "output.svg", precision=4)
```

### Conversion

Transform SVG structure and remove editor-specific data:

```python
from svg_matrix import to_plain_svg, flatten, convert_shapes

# Remove Inkscape/Illustrator namespaces and metadata
to_plain_svg("inkscape.svg", "plain.svg")

# Flatten transforms, groups, and clipPaths into paths
flatten(
    "complex.svg",
    "flat.svg",
    flatten_transforms=True,  # Bake transforms into coordinates
    flatten_groups=True,      # Merge nested groups
    flatten_clipaths=True     # Resolve clipping paths
)

# Convert geometric shapes to <path> elements
convert_shapes("shapes.svg", "paths.svg")
```

### Font Embedding

Make SVGs self-contained by embedding external fonts:

```python
from svg_matrix import run_svgfonts

# List fonts in an SVG
result = run_svgfonts(["list", "input.svg"])
print(result["stdout"])

# Embed fonts with optimal settings
result = run_svgfonts([
    "embed",
    "--woff2",              # Best compression format
    "--subset",             # Only include used glyphs
    "-o", "output.svg",     # Output file
    "input.svg"             # Input file
])

if result["returncode"] == 0:
    print("✓ Fonts embedded successfully!")
else:
    print(f"✗ Error: {result['stderr']}")

# Extract embedded fonts to files
result = run_svgfonts([
    "extract",
    "--extract-dir", "./fonts/",
    "input.svg"
])

# Search for fonts by name
result = run_svgfonts(["search", "--query", "open sans", "--limit", "5"])
```

See `examples/embed_google_fonts.py` for a complete working example.

### Direct CLI Access

Run any CLI command programmatically:

```python
from svg_matrix import run_svgm, run_svg_matrix, run_svgfonts, run_svglinter, get_info

# Run svgm with any arguments
result = run_svgm(["input.svg", "-o", "output.svg", "-p", "4"])
print(result["stdout"])
print(result["stderr"])
print(f"Exit code: {result['returncode']}")

# Get structured SVG info
info = get_info("file.svg")
print(f"Width: {info.get('width')}")
print(f"Height: {info.get('height')}")
print(f"Elements: {info.get('elements')}")
```

### Geometry Functions

Convert geometric shapes to SVG path data:

```python
from svg_matrix import (
    circle_to_path,
    ellipse_to_path,
    rect_to_path,
    line_to_path,
    polygon_to_path,
    polyline_to_path
)

# Convert a circle at (100, 100) with radius 50
path_data = circle_to_path(cx=100, cy=100, r=50)
# Returns: "M 100 50 C 127.614... 50 150 72.386... ..."

# Convert a rectangle
path_data = rect_to_path(x=0, y=0, width=100, height=50)

# Convert with rounded corners
path_data = rect_to_path(x=0, y=0, width=100, height=50, rx=10, ry=10)

# Convert a polygon (list of [x, y] points)
points = [[0, 0], [100, 0], [50, 100]]
path_data = polygon_to_path(points)
```

### Path Manipulation

Parse, transform, and serialize SVG path data:

```python
from svg_matrix import (
    parse_path,
    path_to_string,
    path_to_absolute,
    path_to_cubics,
    transform_path
)

# Parse path string to command list
commands = parse_path("M 0 0 L 100 100 C 50 50 150 150 200 200")
# Returns: [{'command': 'M', 'args': ['0', '0']}, ...]

# Convert relative commands to absolute
absolute_path = path_to_absolute("m 10 10 l 20 20")
# Returns: "M 10 10 L 30 30"

# Convert all commands to cubic Bezier curves
cubic_path = path_to_cubics("M 0 0 L 100 100 Q 50 50 100 0")
# All arcs, lines, quadratics become cubic curves

# Apply transformation matrix to path
from svg_matrix import translate_2d
matrix = translate_2d(50, 100)
transformed = transform_path("M 0 0 L 100 100", matrix)
```

### Transform Matrices

Create and combine 2D transformation matrices:

```python
from svg_matrix import (
    translate_2d,
    rotate_2d,
    scale_2d,
    transform_2d,
    identity,
    multiply_matrices
)
import math

# Create transformation matrices
translate = translate_2d(tx=50, ty=100)      # Move by (50, 100)
rotate = rotate_2d(angle=math.pi / 4)        # Rotate 45 degrees
scale = scale_2d(sx=2, sy=2)                 # Scale 2x

# Combine matrices (applied right-to-left: scale, rotate, translate)
combined = multiply_matrices(translate, multiply_matrices(rotate, scale))

# Apply matrix to a point
x, y = transform_2d(combined, 10, 20)

# Create identity matrix
I = identity(3)  # 3x3 identity matrix
```

### Precision Control

Control decimal precision for arbitrary-precision calculations:

```python
from svg_matrix import set_precision, get_precision, get_kappa

# Get current precision (default: 20 decimal places)
print(f"Current precision: {get_precision()}")

# Set higher precision for scientific applications
set_precision(50)

# Get the kappa constant for circular arc approximation
# (used internally for circle_to_path, etc.)
kappa = get_kappa()
print(f"Kappa: {kappa}")  # ~0.5522847498...
```

---

## Batch Processing

Process multiple SVG files efficiently:

```python
from pathlib import Path
from svg_matrix import validate_svg, optimize_svg

# Process all SVGs in a directory
svg_dir = Path("./input")
output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)

for svg_file in svg_dir.glob("*.svg"):
    # Validate first
    result = validate_svg(svg_file)

    if result["valid"]:
        # Optimize valid files
        optimize_svg(svg_file, output_dir / svg_file.name, precision=4)
        print(f"✓ Optimized: {svg_file.name}")
    else:
        # Report issues
        print(f"✗ Skipped {svg_file.name}:")
        for issue in result["issues"]:
            print(f"  - {issue['reason']}")
```

---

## Examples

The `examples/` directory contains working examples:

| File | Description |
|------|-------------|
| `embed_google_fonts.py` | Complete workflow for embedding Google Fonts |
| `google_fonts_sample.svg` | Sample SVG using Google Fonts via @import |

Run the example:

```bash
cd examples/
python embed_google_fonts.py
```

---

## How It Works

This package is a lightweight Python wrapper (~20KB) around the [@emasoft/svg-matrix](https://www.npmjs.com/package/@emasoft/svg-matrix) npm package.

**Architecture:**
1. Python functions call `bunx` (or `npx` as fallback)
2. The npm package handles all SVG processing
3. Results are returned as Python dictionaries

**Benefits:**
- Always uses the latest svg-matrix version from npm
- Full feature parity with the JavaScript library
- Minimal Python dependencies
- Works on Windows, macOS, and Linux

**Trade-offs:**
- Requires Bun or Node.js runtime
- First run downloads the npm package (~1MB)
- Slightly slower startup than native Python

---

## License

MIT License — see [LICENSE](LICENSE)

## Links

- [GitHub Repository](https://github.com/Emasoft/SVG-MATRIX)
- [npm Package](https://www.npmjs.com/package/@emasoft/svg-matrix)
- [PyPI Package](https://pypi.org/project/svg-matrix/)
- [Issue Tracker](https://github.com/Emasoft/SVG-MATRIX/issues)
