"""Image and chart utility functions for TUI.

This module provides utilities for:
- Opening files with system default applications
- Building mermaid.live URLs for diagram viewing
- Generating chart PNGs with matplotlib
- Rendering mermaid diagrams to PNG
"""
import atexit
import base64
import json
import logging
import platform
import shutil
import subprocess  # nosec B404 - used for system file/URL opening
import tempfile
import zlib
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)

# Track temp directories for cleanup on exit
_temp_directories: Set[Path] = set()


def _cleanup_temp_directories() -> None:
    """Clean up all tracked temp directories on exit."""
    for path in _temp_directories:
        try:
            if path.exists():
                shutil.rmtree(path)
        except Exception as e:
            logger.debug(f"Failed to cleanup temp directory {path}: {e}")


# Register cleanup function to run on exit
atexit.register(_cleanup_temp_directories)


def _create_temp_dir(prefix: str) -> Path:
    """Create a temp directory and track it for cleanup."""
    path = Path(tempfile.mkdtemp(prefix=prefix))
    _temp_directories.add(path)
    return path


def open_file_with_system(path: Path) -> bool:
    """Open a file with the system's default application.

    Args:
        path: Path to the file to open

    Returns:
        True if successful, False otherwise
    """
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(path)], check=True)  # nosec B603 B607
        elif system == "Windows":
            # start is a shell built-in, requires shell=True
            subprocess.run(["start", str(path)], shell=True, check=True)  # nosec B602 B603 B607
        else:  # Linux and others
            subprocess.run(["xdg-open", str(path)], check=True)  # nosec B603 B607
        return True
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return False


def open_url_in_browser(url: str) -> bool:
    """Open a URL in the system's default browser.

    Args:
        url: URL to open

    Returns:
        True if successful, False otherwise
    """
    import webbrowser

    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"Failed to open URL: {e}")
        return False


def build_mermaid_live_url(diagram: str) -> str:
    """Build a mermaid.live URL for viewing a diagram.

    Args:
        diagram: Mermaid diagram source code

    Returns:
        URL to view the diagram on mermaid.live
    """
    try:
        state = {"code": diagram, "mermaid": {"theme": "dark"}}
        state_json = json.dumps(state)
        compressed = zlib.compress(state_json.encode("utf-8"), level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
        return f"https://mermaid.live/edit#pako:{encoded}"
    except Exception as e:
        logger.debug(f"Failed to build mermaid.live URL: {e}")
        return "https://mermaid.live"


def render_mermaid_to_png(diagram: str, output_dir: Optional[Path] = None) -> Optional[Path]:
    """Render a mermaid diagram to PNG.

    Args:
        diagram: Mermaid diagram source code
        output_dir: Directory to save the PNG (temp dir if None)

    Returns:
        Path to the PNG file, or None if rendering failed
    """
    if output_dir is None:
        output_dir = _create_temp_dir(prefix="mermaid_")

    mmd_path = output_dir / "diagram.mmd"
    png_path = output_dir / "diagram.png"

    mmd_path.write_text(diagram)

    # Try mermaid-cli Python API
    try:
        from mermaid_cli import render_mermaid_file_sync  # type: ignore

        render_mermaid_file_sync(
            input_file=str(mmd_path),
            output_file=str(png_path),
            output_format="png",
        )
        if png_path.exists():
            return png_path
    except Exception as e:
        logger.debug(f"mermaid_cli render failed: {e}")

    # Try mmdc CLI
    mmdc = shutil.which("mmdc")
    if mmdc:
        try:
            subprocess.run(  # nosec B603 - mmdc path from shutil.which, args are internal
                [
                    mmdc,
                    "-i", str(mmd_path),
                    "-o", str(png_path),
                    "-b", "transparent",
                    "-s", "4",  # Scale factor for higher resolution
                    "-w", "2400",  # Width in pixels
                ],
                check=True,
                capture_output=True,
            )
            if png_path.exists():
                return png_path
        except Exception as e:
            logger.debug(f"mmdc render failed: {e}")

    return None


def render_chart_to_png(
    chart_type: str,
    title: str,
    x_data: list,
    y_data: list,
    x_label: str = "",
    y_label: str = "",
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Render chart data to PNG using matplotlib.

    Args:
        chart_type: Type of chart (bar, line, scatter, pie, area)
        title: Chart title
        x_data: X-axis data
        y_data: Y-axis data
        x_label: X-axis label
        y_label: Y-axis label
        output_dir: Directory to save the PNG (temp dir if None)

    Returns:
        Path to the PNG file, or None if rendering failed
    """
    if output_dir is None:
        output_dir = _create_temp_dir(prefix="chart_")

    png_path = output_dir / "chart.png"

    try:
        import matplotlib

        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))

        # Apply dark theme
        plt.style.use("dark_background")

        if chart_type == "bar":
            ax.bar(range(len(x_data)), y_data, color="#4a9eff")
            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels(
                [str(x)[:15] for x in x_data], rotation=45, ha="right"
            )
        elif chart_type == "scatter":
            ax.scatter(range(len(x_data)), y_data, color="#4a9eff", alpha=0.7)
            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels(
                [str(x)[:15] for x in x_data], rotation=45, ha="right"
            )
        elif chart_type == "pie":
            ax.pie(y_data, labels=x_data, autopct="%1.1f%%")
        elif chart_type == "area":
            ax.fill_between(range(len(x_data)), y_data, alpha=0.5, color="#4a9eff")
            ax.plot(range(len(x_data)), y_data, color="#4a9eff")
            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels(
                [str(x)[:15] for x in x_data], rotation=45, ha="right"
            )
        else:  # line (default)
            ax.plot(range(len(x_data)), y_data, color="#4a9eff", linewidth=2)
            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels(
                [str(x)[:15] for x in x_data], rotation=45, ha="right"
            )

        ax.set_title(title, fontsize=14, fontweight="bold")
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)

        plt.tight_layout()
        # Use higher DPI for crisp rendering
        plt.savefig(png_path, dpi=300, facecolor="#1a1a1a", edgecolor="none")
        plt.close(fig)

        return png_path

    except ImportError:
        logger.debug("matplotlib not available for chart rendering")
    except Exception as e:
        logger.error(f"Failed to render chart: {e}")

    return None
