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
"""

__version__ = "1.3.8"

from svg_matrix.cli import get_info, run_svg_matrix, run_svgm
from svg_matrix.conversion import convert_shapes, flatten, to_plain_svg
from svg_matrix.optimization import optimize_paths, optimize_svg
from svg_matrix.validation import validate_svg, validate_svg_async

__all__ = [
    # Version
    "__version__",
    "convert_shapes",
    "flatten",
    "get_info",
    "optimize_paths",
    # Optimization
    "optimize_svg",
    "run_svg_matrix",
    # CLI access
    "run_svgm",
    # Conversion
    "to_plain_svg",
    # Validation
    "validate_svg",
    "validate_svg_async",
]
