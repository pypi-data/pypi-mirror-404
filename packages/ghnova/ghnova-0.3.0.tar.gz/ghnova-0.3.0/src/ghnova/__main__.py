"""Main entry point for the ghnova package."""

from __future__ import annotations

if __name__ == "__main__":
    from ghnova.utils.log import setup_logger

    setup_logger(print_version=True)
