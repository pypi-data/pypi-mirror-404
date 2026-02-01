"""
Command-line interface for ppget.

This module provides the main CLI entry point for the ppget tool.
"""

import argparse
import logging
import re
import sys
from datetime import datetime

from .output import determine_output_path, save_metadata, save_to_csv, save_to_json
from .search import search_pubmed

# Suppress debug logs from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)


def validate_limit(limit: int) -> None:
    """Validate the limit parameter."""
    if limit <= 0:
        raise ValueError("Limit must be a positive number")
    if limit > 10000:
        raise ValueError("Limit cannot exceed 10000 (API limitation)")


def validate_email(email: str) -> None:
    """Basic email validation."""
    if email == "anonymous@example.com":
        return  # Default value is OK

    # Simple email pattern check
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")


def main():
    from ppget import __version__

    parser = argparse.ArgumentParser(description="A simple CLI tool to download PubMed articles")
    parser.add_argument(
        "query", type=str, help="Search query (e.g., 'machine learning AND medicine')"
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=100,
        help="Maximum number of results to retrieve (default: 100)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output file path or directory (default: current directory)",
    )
    parser.add_argument(
        "-e",
        "--email",
        type=str,
        default="anonymous@example.com",
        help="Email address for API rate limit relaxation (default: anonymous@example.com)",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress progress messages (errors only)"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"ppget {__version__}",
        help="Show version and exit",
    )

    args = parser.parse_args()

    # Auto-detect format from output file extension if not explicitly specified
    format_explicitly_set = "--format" in sys.argv or "-f" in sys.argv
    if args.output and not format_explicitly_set:
        if args.output.endswith(".json"):
            args.format = "json"
        elif args.output.endswith(".csv"):
            args.format = "csv"

    # Validate format matches extension if both are specified
    if args.output and format_explicitly_set:
        if args.output.endswith(".json") and args.format != "json":
            print(
                f"Error: File extension '.json' doesn't match format "
                f"'{args.format}'. Expected '.{args.format}'",
                file=sys.stderr,
            )
            return 1
        elif args.output.endswith(".csv") and args.format != "csv":
            print(
                f"Error: File extension '.csv' doesn't match format "
                f"'{args.format}'. Expected '.{args.format}'",
                file=sys.stderr,
            )
            return 1

    # Validate inputs
    try:
        validate_limit(args.limit)
        validate_email(args.email)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Start search
    if not args.quiet:
        print("Searching PubMed...")
        print(f"Query: '{args.query}'")
        print(f"Max results: {args.limit}")

    try:
        search_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        articles = search_pubmed(args.query, args.limit, args.email, args.quiet)

        if not args.quiet:
            print(f"✓ Found {len(articles)} articles")

        if not articles:
            if not args.quiet:
                print("No articles found for the given query")
            return 0

        # Determine output path
        output_path = determine_output_path(args.output, args.format)

        # Save data based on format
        if args.format == "json":
            save_to_json(articles, output_path)
        else:  # csv
            save_to_csv(articles, output_path)

        # Always save metadata to .meta.txt
        meta_path = save_metadata(args.query, len(articles), output_path, search_date)

        if not args.quiet:
            print(f"✓ Saved {len(articles)} articles to {output_path}")
            print(f"✓ Metadata saved to {meta_path}")
            print(f"\nSuccessfully downloaded {len(articles)} articles")

    except KeyboardInterrupt:
        print("\nSearch cancelled by user", file=sys.stderr)
        return 130
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"File error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback

            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
