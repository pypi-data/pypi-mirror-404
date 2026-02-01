# ────────────────────────────────────────────────────────────────────────────────────────
#   scanner.py
#   ──────────
#
#   Scans directories for Python files and collects statistics.
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

from dataclasses import dataclass
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────────────
#   Data Classes
# ────────────────────────────────────────────────────────────────────────────────────────


@dataclass
class PyStats:
    """Statistics for Python files in a directory."""

    num_files: int
    total_bytes: int
    total_lines: int
    code_lines: int

    @property
    def total_kb(self) -> float:
        """Return total size in kilobytes."""
        return self.total_bytes / 1024


# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def is_code_line(line: str) -> bool:
    """Determine if a line is a code line (not blank or comment)."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return False
    return True


# ────────────────────────────────────────────────────────────────────────────────────────
def count_lines(filepath: Path) -> tuple[int, int]:
    """
    Count total lines and code lines in a file.

    Returns:
        Tuple of (total_lines, code_lines).
    """
    total_lines = 0
    code_lines = 0
    in_multiline_string = False
    multiline_char: str | None = None

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, 0

    for line in content.splitlines():
        total_lines += 1
        stripped = line.strip()

        # Handle multiline strings (docstrings)
        if in_multiline_string:
            if multiline_char and multiline_char in stripped:
                in_multiline_string = False
                multiline_char = None
            continue

        # Check for start of multiline string
        if stripped.startswith('"""') or stripped.startswith("'''"):
            quote = stripped[:3]
            # Check if it ends on the same line
            rest = stripped[3:]
            if quote not in rest:
                in_multiline_string = True
                multiline_char = quote
            continue

        if is_code_line(line):
            code_lines += 1

    return total_lines, code_lines


# ────────────────────────────────────────────────────────────────────────────────────────
def is_in_hidden_dir(filepath: Path, base: Path) -> bool:
    """Check if the file is inside a hidden directory (starting with dot)."""
    relative = filepath.relative_to(base)
    return any(part.startswith(".") for part in relative.parts[:-1])


# ────────────────────────────────────────────────────────────────────────────────────────
def scan_directory(directory: Path) -> PyStats:
    """
    Scan a directory recursively for Python files and collect statistics.

    Skips hidden directories (those starting with a dot, e.g. .venv, .git).

    Args:
        directory: The directory to scan.

    Returns:
        PyStats object containing the collected statistics.
    """
    num_files = 0
    total_bytes = 0
    total_lines = 0
    code_lines = 0

    for filepath in directory.rglob("*.py"):
        if not filepath.is_file():
            continue

        # Skip files in hidden directories
        if is_in_hidden_dir(filepath, directory):
            continue

        num_files += 1

        try:
            total_bytes += filepath.stat().st_size
        except OSError:
            pass

        lines, code = count_lines(filepath)
        total_lines += lines
        code_lines += code

    return PyStats(
        num_files=num_files,
        total_bytes=total_bytes,
        total_lines=total_lines,
        code_lines=code_lines,
    )
