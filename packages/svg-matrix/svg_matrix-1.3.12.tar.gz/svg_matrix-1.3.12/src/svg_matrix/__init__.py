"""
svg-matrix: Python wrapper for svg-matrix SVG processing library.

This package provides Python bindings to the svg-matrix Node.js library,
enabling arbitrary-precision SVG optimization, validation, and manipulation.

Example usage:
    from svg_matrix import validate_svg, optimize_svg, to_plain_svg

    # Validate an SVG file
    result = validate_svg("icon.svg")
    if result["valid"]:
        print("SVG is valid!")

    # Optimize an SVG file
    optimize_svg("input.svg", "output.svg")

    # Convert Inkscape SVG to plain SVG
    to_plain_svg("inkscape.svg", "plain.svg")

    # Use library functions directly
    from svg_matrix import circle_to_path, translate_2d, transform_path
    path = circle_to_path(100, 100, 50)
    matrix = translate_2d(10, 20)
    transformed = transform_path(path, matrix)
"""

__version__ = "1.3.12"

from svg_matrix.cli import get_info, run_svg_matrix, run_svgm
from svg_matrix.conversion import convert_shapes, flatten, to_plain_svg
from svg_matrix.library import (
    circle_to_path,
    ellipse_to_path,
    get_kappa,
    get_precision,
    identity,
    line_to_path,
    multiply_matrices,
    parse_path,
    path_to_absolute,
    path_to_cubics,
    path_to_string,
    polygon_to_path,
    polyline_to_path,
    process_svg,
    rect_to_path,
    rotate_2d,
    run_browser_verification,
    scale_2d,
    set_precision,
    transform_2d,
    transform_path,
    translate_2d,
    verify_matrix_against_browser,
)
from svg_matrix.optimization import optimize_paths, optimize_svg
from svg_matrix.validation import validate_svg, validate_svg_async

__all__ = [
    # Version
    "__version__",
    # Geometry to Path
    "circle_to_path",
    # SVG Processing
    "convert_shapes",
    "ellipse_to_path",
    "flatten",
    # CLI access
    "get_info",
    # Precision
    "get_kappa",
    "get_precision",
    # 2D Transforms
    "identity",
    "line_to_path",
    "multiply_matrices",
    "optimize_paths",
    "optimize_svg",
    # Path Manipulation
    "parse_path",
    "path_to_absolute",
    "path_to_cubics",
    "path_to_string",
    "polygon_to_path",
    "polyline_to_path",
    "process_svg",
    "rect_to_path",
    "rotate_2d",
    "run_browser_verification",
    "run_svg_matrix",
    "run_svgm",
    "scale_2d",
    "set_precision",
    "to_plain_svg",
    "transform_2d",
    "transform_path",
    "translate_2d",
    # Validation
    "validate_svg",
    "validate_svg_async",
    # Browser Verification
    "verify_matrix_against_browser",
]
