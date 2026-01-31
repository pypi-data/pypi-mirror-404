"""
Python wrapper for svg-matrix library functions.

Provides Python bindings to the core svg-matrix JavaScript library functions,
enabling arbitrary-precision geometry operations, path manipulation, and
SVG transformations from Python.

Example usage:
    from svg_matrix.library import (
        circle_to_path, rect_to_path, parse_path, transform_path,
        translate_2d, rotate_2d, scale_2d
    )

    # Convert a circle to SVG path data
    path = circle_to_path(cx=100, cy=100, r=50)
    print(path)  # "M 150 100 C 150 127.614... ..."

    # Parse and transform a path
    commands = parse_path("M 0 0 L 100 100")
    matrix = translate_2d(50, 50)
    transformed = transform_path("M 0 0 L 100 100", matrix)
"""

import json
import subprocess
from typing import Any, Optional

from svg_matrix._runtime import ensure_runtime

# Default precision for decimal operations
DEFAULT_PRECISION = 6


def _run_lib_script(script: str, timeout: int = 30) -> Any:
    """
    Run an inline JavaScript script that uses the svg-matrix library.

    Args:
        script: JavaScript code to execute (should output JSON to stdout)
        timeout: Timeout in seconds

    Returns:
        Parsed JSON output from the script
    """
    import shutil

    ensure_runtime()

    # Wrap script to import library and output JSON
    full_script = f"""
import('@emasoft/svg-matrix').then(lib => {{
    {script}
}}).catch(e => {{
    console.error(JSON.stringify({{error: e.message}}));
    process.exit(1);
}});
"""

    # Prefer bun over node for better performance
    runtime = "bun" if shutil.which("bun") else "node"

    result = subprocess.run(
        [runtime, "-e", full_script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() or "Unknown error"
        raise RuntimeError(f"Script execution failed: {error_msg}")

    output = result.stdout.strip()
    if output:
        data: Any = json.loads(output)
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(data["error"])
        return data
    return None


# =============================================================================
# Geometry to Path Functions
# =============================================================================


def circle_to_path(
    cx: float, cy: float, r: float, precision: int = DEFAULT_PRECISION
) -> str:
    """
    Convert a circle to SVG path data.

    Args:
        cx: Center X coordinate
        cy: Center Y coordinate
        r: Radius
        precision: Decimal precision for output coordinates

    Returns:
        SVG path data string (e.g., "M 150 100 C 150 127.614...")
    """
    script = f"""
const path = lib.circleToPath({cx}, {cy}, {r}, {precision});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def ellipse_to_path(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    precision: int = DEFAULT_PRECISION,
) -> str:
    """
    Convert an ellipse to SVG path data.

    Args:
        cx: Center X coordinate
        cy: Center Y coordinate
        rx: X radius
        ry: Y radius
        precision: Decimal precision for output coordinates

    Returns:
        SVG path data string
    """
    script = f"""
const path = lib.ellipseToPath({cx}, {cy}, {rx}, {ry}, {precision});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def rect_to_path(
    x: float,
    y: float,
    width: float,
    height: float,
    rx: float = 0,
    ry: float = 0,
    precision: int = DEFAULT_PRECISION,
) -> str:
    """
    Convert a rectangle to SVG path data.

    Args:
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Rectangle width
        height: Rectangle height
        rx: X radius for rounded corners (default: 0)
        ry: Y radius for rounded corners (default: 0)
        precision: Decimal precision for output coordinates

    Returns:
        SVG path data string
    """
    script = f"""
const path = lib.rectToPath({x}, {y}, {width}, {height}, {rx}, {ry}, {precision});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def line_to_path(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    precision: int = DEFAULT_PRECISION,
) -> str:
    """
    Convert a line to SVG path data.

    Args:
        x1: Start X coordinate
        y1: Start Y coordinate
        x2: End X coordinate
        y2: End Y coordinate
        precision: Decimal precision for output coordinates

    Returns:
        SVG path data string (e.g., "M 0 0 L 100 100")
    """
    script = f"""
const path = lib.lineToPath({x1}, {y1}, {x2}, {y2}, {precision});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def polygon_to_path(
    points: list[tuple[float, float]], precision: int = DEFAULT_PRECISION
) -> str:
    """
    Convert a polygon to SVG path data.

    Args:
        points: List of (x, y) coordinate tuples
        precision: Decimal precision for output coordinates

    Returns:
        SVG path data string (closed path)
    """
    points_str = json.dumps([[p[0], p[1]] for p in points])
    script = f"""
const path = lib.polygonToPath({points_str}, {precision});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def polyline_to_path(
    points: list[tuple[float, float]], precision: int = DEFAULT_PRECISION
) -> str:
    """
    Convert a polyline to SVG path data.

    Args:
        points: List of (x, y) coordinate tuples
        precision: Decimal precision for output coordinates

    Returns:
        SVG path data string (open path)
    """
    points_str = json.dumps([[p[0], p[1]] for p in points])
    script = f"""
const path = lib.polylineToPath({points_str}, {precision});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


# =============================================================================
# Path Manipulation Functions
# =============================================================================


def parse_path(path_data: str) -> list[dict[str, Any]]:
    """
    Parse SVG path data into a list of path commands.

    Args:
        path_data: SVG path data string (e.g., "M 0 0 L 100 100 Z")

    Returns:
        List of command dictionaries with 'command' and coordinate keys
    """
    script = f"""
const commands = lib.parsePath({json.dumps(path_data)});
console.log(JSON.stringify(commands));
"""
    result: list[dict[str, Any]] = _run_lib_script(script)
    return result


def path_to_string(
    commands: list[dict[str, Any]], precision: int = DEFAULT_PRECISION
) -> str:
    """
    Convert parsed path commands back to SVG path data string.

    Args:
        commands: List of command dictionaries from parse_path()
        precision: Decimal precision for output coordinates

    Returns:
        SVG path data string
    """
    script = f"""
const path = lib.pathToString({json.dumps(commands)}, {precision});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def path_to_absolute(path_data: str) -> str:
    """
    Convert all path commands to absolute coordinates.

    Args:
        path_data: SVG path data string with relative or mixed commands

    Returns:
        SVG path data string with only absolute commands
    """
    script = f"""
const path = lib.pathToAbsolute({json.dumps(path_data)});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def path_to_cubics(path_data: str) -> str:
    """
    Convert all path commands to cubic Bezier curves.

    Args:
        path_data: SVG path data string

    Returns:
        SVG path data string with only M, C, and Z commands
    """
    script = f"""
const path = lib.pathToCubics({json.dumps(path_data)});
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


def transform_path(
    path_data: str,
    matrix: list[list[float]],
    precision: int = DEFAULT_PRECISION,
) -> str:
    """
    Apply a transformation matrix to path data.

    Args:
        path_data: SVG path data string
        matrix: 3x3 transformation matrix as nested list
        precision: Decimal precision for output coordinates

    Returns:
        Transformed SVG path data string
    """
    script = f"""
const path = lib.transformPath(
    {json.dumps(path_data)},
    {json.dumps(matrix)},
    {precision}
);
console.log(JSON.stringify(path));
"""
    result: str = _run_lib_script(script)
    return result


# =============================================================================
# 2D Transform Functions
# =============================================================================


def translate_2d(tx: float, ty: float) -> list[list[float]]:
    """
    Create a 2D translation matrix.

    Args:
        tx: X translation
        ty: Y translation

    Returns:
        3x3 transformation matrix as nested list
    """
    script = f"""
const m = lib.translate2D({tx}, {ty});
// Convert Matrix.data (Decimal values) to numbers
const arr = m.data.map(row => row.map(v => Number(v)));
console.log(JSON.stringify(arr));
"""
    result: list[list[float]] = _run_lib_script(script)
    return result


def rotate_2d(angle: float) -> list[list[float]]:
    """
    Create a 2D rotation matrix.

    Args:
        angle: Rotation angle in radians

    Returns:
        3x3 transformation matrix as nested list
    """
    script = f"""
const m = lib.rotate2D({angle});
const arr = m.data.map(row => row.map(v => Number(v)));
console.log(JSON.stringify(arr));
"""
    result: list[list[float]] = _run_lib_script(script)
    return result


def scale_2d(sx: float, sy: Optional[float] = None) -> list[list[float]]:
    """
    Create a 2D scaling matrix.

    Args:
        sx: X scale factor
        sy: Y scale factor (defaults to sx for uniform scaling)

    Returns:
        3x3 transformation matrix as nested list
    """
    sy_arg = sy if sy is not None else sx
    script = f"""
const m = lib.scale2D({sx}, {sy_arg});
const arr = m.data.map(row => row.map(v => Number(v)));
console.log(JSON.stringify(arr));
"""
    result: list[list[float]] = _run_lib_script(script)
    return result


def transform_2d(
    matrix: list[list[float]], x: float, y: float
) -> tuple[float, float]:
    """
    Apply a 2D transformation matrix to a point.

    Args:
        matrix: 3x3 transformation matrix as nested list
        x: X coordinate
        y: Y coordinate

    Returns:
        Tuple of (transformed_x, transformed_y)
    """
    script = f"""
const [tx, ty] = lib.transform2D({json.dumps(matrix)}, {x}, {y});
console.log(JSON.stringify([Number(tx), Number(ty)]));
"""
    result: list[float] = _run_lib_script(script)
    return (result[0], result[1])


def identity(n: int = 3) -> list[list[float]]:
    """
    Create an identity matrix.

    Args:
        n: Matrix dimension (default: 3 for 2D transforms)

    Returns:
        n x n identity matrix as nested list
    """
    script = f"""
const m = lib.identity({n});
const arr = m.data.map(row => row.map(v => Number(v)));
console.log(JSON.stringify(arr));
"""
    result: list[list[float]] = _run_lib_script(script)
    return result


def multiply_matrices(
    a: list[list[float]], b: list[list[float]]
) -> list[list[float]]:
    """
    Multiply two matrices.

    Args:
        a: First matrix as nested list
        b: Second matrix as nested list

    Returns:
        Result matrix as nested list
    """
    script = f"""
const mA = lib.mat({json.dumps(a)});
const mB = lib.mat({json.dumps(b)});
const result = mA.mul(mB);
const arr = result.data.map(row => row.map(v => Number(v)));
console.log(JSON.stringify(arr));
"""
    result: list[list[float]] = _run_lib_script(script)
    return result


# =============================================================================
# Precision Functions
# =============================================================================


def get_kappa() -> float:
    """
    Get the kappa constant for circular arc approximation with cubic Beziers.

    Returns:
        Kappa value (approximately 0.5522847498)
    """
    script = """
const k = lib.getKappa();
console.log(JSON.stringify(Number(k)));
"""
    result: float = _run_lib_script(script)
    return result


def set_precision(precision: int) -> None:
    """
    Set the global decimal precision for the library.

    Args:
        precision: Number of significant digits (1-1000000000)
    """
    script = f"""
lib.setPrecision({precision});
console.log(JSON.stringify(true));
"""
    _run_lib_script(script)


def get_precision() -> int:
    """
    Get the current global decimal precision.

    Returns:
        Current precision setting
    """
    script = """
const p = lib.getPrecision();
console.log(JSON.stringify(p));
"""
    result: int = _run_lib_script(script)
    return result


# =============================================================================
# SVG Processing Functions
# =============================================================================


def process_svg(
    svg_content: str,
    operations: list[str],
    precision: int = DEFAULT_PRECISION,
) -> str:
    """
    Process SVG content with a list of operations.

    Args:
        svg_content: SVG content as string
        operations: List of operation names to apply (e.g., ["convertShapesToPaths",
            "flattenTransforms", "removeHiddenElements"])
        precision: Decimal precision for output

    Returns:
        Processed SVG content as string

    Available operations:
        - convertShapesToPaths: Convert rect, circle, ellipse, etc. to paths
        - flattenTransforms: Bake transforms into coordinates
        - removeHiddenElements: Remove display:none and visibility:hidden elements
        - removeEmptyGroups: Remove empty <g> elements
        - removeComments: Remove XML comments
        - removeMetadata: Remove metadata elements
        - cleanupIds: Remove unused IDs
        - mergeStyles: Consolidate inline styles
        - optimizePaths: Optimize path data
    """
    ops_str = json.dumps(operations)
    script = f"""
const {{ JSDOM }} = await import('jsdom');
const dom = new JSDOM({json.dumps(svg_content)}, {{ contentType: 'image/svg+xml' }});
const doc = dom.window.document;
const svg = doc.querySelector('svg');

if (!svg) {{
    throw new Error('No SVG element found');
}}

// Apply operations
for (const op of {ops_str}) {{
    if (typeof lib.SVGToolbox[op] === 'function') {{
        lib.SVGToolbox[op](svg, doc, {{ precision: {precision} }});
    }}
}}

// Serialize back to string
const serializer = new dom.window.XMLSerializer();
const result = serializer.serializeToString(svg);
console.log(JSON.stringify(result));
"""
    result: str = _run_lib_script(script, timeout=60)
    return result
