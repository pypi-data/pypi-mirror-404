# ────────────────────────────────────────────────────────────────────────────────────────
#   __init__.py
#   ───────────
#
#   cal-pystats package initialisation.
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

"""cal-pystats: A CLI tool to analyse Python file statistics in a directory."""

__all__ = ["__version__"]

try:
    from importlib.metadata import version

    __version__ = version("cal-pystats")
except Exception:
    __version__ = "0.0.0+unknown"
