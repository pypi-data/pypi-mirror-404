# ────────────────────────────────────────────────────────────────────────────────────────
#   output.py
#   ─────────
#
#   Output formatting with ASCII box and optional ANSI colour support.
#
#   (c) 2026 Cyber Assessment Labs — MIT License; see LICENSE in the project root.
#
#   Authors
#   ───────
#   bena (via Claude)
#
#   Version History
#   ───────────────
#   Jan 2026 - Created
# ────────────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────────────
#   Imports
# ────────────────────────────────────────────────────────────────────────────────────────

import json
import sys
from pathlib import Path
from typing import Literal
from cal_pystats.scanner import PyStats

# ────────────────────────────────────────────────────────────────────────────────────────
#   Constants
# ────────────────────────────────────────────────────────────────────────────────────────

# ANSI colour codes
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"

# Box drawing characters
BOX_TOP_LEFT = "╭"
BOX_TOP_RIGHT = "╮"
BOX_BOTTOM_LEFT = "╰"
BOX_BOTTOM_RIGHT = "╯"
BOX_HORIZONTAL = "─"
BOX_VERTICAL = "│"

# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def use_colour() -> bool:
    """Determine if ANSI colour should be used."""
    return sys.stdout.isatty()


# ────────────────────────────────────────────────────────────────────────────────────────
def colour(text: str, *codes: str) -> str:
    """Apply ANSI colour codes to text if output is a terminal."""
    if not use_colour():
        return text
    return "".join(codes) + text + RESET


# ────────────────────────────────────────────────────────────────────────────────────────
def format_size(kb: float) -> str:
    """Format size with appropriate unit."""
    if kb >= 1024:
        return f"{kb / 1024:.2f} MB"
    return f"{kb:.2f} KB"


# ────────────────────────────────────────────────────────────────────────────────────────
def format_number(n: int) -> str:
    """Format number with thousand separators."""
    return f"{n:,}"


# ────────────────────────────────────────────────────────────────────────────────────────
def display_stats(
    stats: PyStats, directory: Path, output_format: Literal["box", "plain", "json"]
) -> None:
    """Display statistics in the specified format."""
    if output_format == "json":
        display_json(stats, directory)
    elif output_format == "plain":
        display_plain(stats, directory)
    else:
        display_box(stats, directory)


# ────────────────────────────────────────────────────────────────────────────────────────
def display_json(stats: PyStats, directory: Path) -> None:
    """Display statistics as JSON."""
    data = {
        "directory": directory.name,
        "files": stats.num_files,
        "total_bytes": stats.total_bytes,
        "total_kb": round(stats.total_kb, 2),
        "total_lines": stats.total_lines,
        "code_lines": stats.code_lines,
    }
    print(json.dumps(data, indent=2))


# ────────────────────────────────────────────────────────────────────────────────────────
def display_plain(stats: PyStats, directory: Path) -> None:
    """Display statistics as plain text."""
    print(f"Python Stats: {directory.name}")
    print(f"Files: {format_number(stats.num_files)}")
    print(f"Total Size: {format_size(stats.total_kb)}")
    print(f"Total Lines: {format_number(stats.total_lines)}")
    print(f"Code Lines: {format_number(stats.code_lines)}")


# ────────────────────────────────────────────────────────────────────────────────────────
def display_box(stats: PyStats, directory: Path) -> None:
    """Display statistics in a formatted ASCII box."""
    # Prepare the content lines
    title = f" Python Stats: {directory.name} "
    lines = [
        ("Files", format_number(stats.num_files), CYAN),
        ("Total Size", format_size(stats.total_kb), GREEN),
        ("Total Lines", format_number(stats.total_lines), YELLOW),
        ("Code Lines", format_number(stats.code_lines), MAGENTA),
    ]

    # Calculate box width
    label_width = max(len(label) for label, _, _ in lines)
    value_width = max(len(value) for _, value, _ in lines)
    content_width = label_width + value_width + 5  # " : " + padding
    box_width = max(len(title), content_width) + 4

    # Build the box
    top_border = BOX_TOP_LEFT + BOX_HORIZONTAL * (box_width - 2) + BOX_TOP_RIGHT
    bottom_border = (
        BOX_BOTTOM_LEFT + BOX_HORIZONTAL * (box_width - 2) + BOX_BOTTOM_RIGHT
    )

    # Print header
    print()
    print(colour(top_border, BOLD))

    # Title line
    title_padded = title.center(box_width - 2)
    print(
        colour(BOX_VERTICAL, BOLD)
        + colour(title_padded, BOLD, CYAN)
        + colour(BOX_VERTICAL, BOLD)
    )

    # Separator
    separator = BOX_VERTICAL + BOX_HORIZONTAL * (box_width - 2) + BOX_VERTICAL
    print(colour(separator, BOLD))

    # Data lines - calculate inner width for proper alignment
    inner_width = box_width - 2  # Width between vertical bars
    for label, value, col in lines:
        padded_label = label.ljust(label_width)
        padded_value = value.rjust(value_width)
        # Build content and pad to fill inner width
        content = f"  {padded_label} : {padded_value}"
        content_padded = content.ljust(inner_width)
        if use_colour():
            # For coloured output, we need to apply colour to value only
            content_plain = f"  {padded_label} : "
            content_padded = content_plain + colour(padded_value, BOLD, col)
            # Pad the rest after the value
            padding_needed = inner_width - len(content_plain) - len(padded_value)
            content_padded += " " * padding_needed
            print(
                colour(BOX_VERTICAL, BOLD) + content_padded + colour(BOX_VERTICAL, BOLD)
            )
        else:
            print(BOX_VERTICAL + content_padded + BOX_VERTICAL)

    # Footer
    print(colour(bottom_border, BOLD))
    print()
