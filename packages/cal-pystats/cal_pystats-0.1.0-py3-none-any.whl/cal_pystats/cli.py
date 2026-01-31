# ────────────────────────────────────────────────────────────────────────────────────────
#   cli.py
#   ──────
#
#   Command-line interface entry point for cal-pystats.
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

import argparse
import sys
from pathlib import Path
from cal_pystats import __version__
from cal_pystats.output import display_stats
from cal_pystats.scanner import scan_directory

# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="cal-pystats",
        description="Analyse Python file statistics in a directory.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Output format options (mutually exclusive)
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--plain",
        action="store_true",
        help="Plain text output (no box or colours)",
    )
    format_group.add_argument(
        "--json",
        action="store_true",
        help="JSON output",
    )

    return parser.parse_args(argv)


# ────────────────────────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    """Main entry point for cal-pystats CLI."""
    args = parse_args(argv)
    directory = Path(args.directory).resolve()

    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist.", file=sys.stderr)
        return 1

    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory.", file=sys.stderr)
        return 1

    # Determine output format
    if args.json:
        output_format = "json"
    elif args.plain:
        output_format = "plain"
    else:
        output_format = "box"

    stats = scan_directory(directory)
    display_stats(stats, directory, output_format)
    return 0


# ────────────────────────────────────────────────────────────────────────────────────────
#   Main
# ────────────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(main())
