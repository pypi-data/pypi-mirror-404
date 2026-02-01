#!/usr/bin/env python3
"""
Main entry point for ppget.

This module provides an alternative entry point for running ppget directly
with `python main.py` instead of using the installed CLI command.

Usage:
    python main.py "search query" [options]

Example:
    python main.py "machine learning" -l 50 -f json
"""

from ppget.cli import main

if __name__ == "__main__":
    exit(main())
