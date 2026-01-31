"""
CLI wrapper functions and entry points.

Provides direct access to the svg-matrix CLI tools from Python.
These entry points mirror the exact options and flags of the original
Node.js/Bun CLI tools.

CLI Commands (installed via pip):
    psvgm       - SVG optimization (mirrors: svgm)
    psvg-matrix - SVG matrix operations (mirrors: svg-matrix)
    psvgfonts   - SVG font operations (mirrors: svgfonts)
    psvglinter  - SVG linting (mirrors: svglinter)
"""

import json
import sys
from pathlib import Path
from typing import Any, Union

from svg_matrix._runtime import ensure_runtime, run_command


def run_svgm(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    """
    Run the svgm CLI with given arguments.

    Args:
        args: Command-line arguments (e.g., ["input.svg", "-o", "output.svg"])
        timeout: Timeout in seconds

    Returns:
        Dictionary with:
        - returncode (int): Process return code
        - stdout (str): Standard output
        - stderr (str): Standard error

    Example:
        >>> result = run_svgm(["--help"])
        >>> print(result["stdout"])
    """
    try:
        result = run_command(["svgm", *args], timeout=timeout)
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }


def run_svg_matrix(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    """
    Run the svg-matrix CLI with given arguments.

    Args:
        args: Command-line arguments (e.g., ["info", "file.svg"])
        timeout: Timeout in seconds

    Returns:
        Dictionary with returncode, stdout, stderr
    """
    try:
        result = run_command(["svg-matrix", *args], timeout=timeout)
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }


def get_info(svg_path: Union[str, Path]) -> dict[str, Any]:
    """
    Get information about an SVG file.

    Args:
        svg_path: Path to SVG file

    Returns:
        Dictionary with SVG information (dimensions, element counts, etc.)
    """
    result = run_svg_matrix(["info", str(svg_path)])

    if result["returncode"] == 0:
        try:
            data: dict[str, Any] = json.loads(result["stdout"])
            return data
        except json.JSONDecodeError:
            return {"raw_output": result["stdout"]}

    return {"error": result["stderr"] or "Failed to get info"}


# CLI entry points for pyproject.toml scripts
# These pass through all arguments to the underlying Node.js CLI


def svgm_main() -> None:
    """
    Entry point for psvgm command.

    Mirrors the svgm CLI exactly - all arguments are passed through.
    Usage: psvgm [options] <input> [-o <output>]
    """
    ensure_runtime()
    result = run_svgm(sys.argv[1:], timeout=300)
    if result["stdout"]:
        sys.stdout.write(result["stdout"])
    if result["stderr"]:
        sys.stderr.write(result["stderr"])
    sys.exit(result["returncode"])


def svg_matrix_main() -> None:
    """
    Entry point for psvg-matrix command.

    Mirrors the svg-matrix CLI exactly - all arguments are passed through.
    Usage: psvg-matrix <command> [options] <input> [-o <output>]
    """
    ensure_runtime()
    result = run_svg_matrix(sys.argv[1:], timeout=300)
    if result["stdout"]:
        sys.stdout.write(result["stdout"])
    if result["stderr"]:
        sys.stderr.write(result["stderr"])
    sys.exit(result["returncode"])


def svgfonts_main() -> None:
    """
    Entry point for psvgfonts command.

    Mirrors the svgfonts CLI exactly - all arguments are passed through.
    Usage: psvgfonts <command> [options] <input> [-o <output>]
    """
    ensure_runtime()
    try:
        result = run_command(["svgfonts", *sys.argv[1:]], timeout=300)
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


def svglinter_main() -> None:
    """
    Entry point for psvglinter command.

    Mirrors the svglinter CLI exactly - all arguments are passed through.
    Usage: psvglinter [options] <input>
    """
    ensure_runtime()
    try:
        result = run_command(["svglinter", *sys.argv[1:]], timeout=300)
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
