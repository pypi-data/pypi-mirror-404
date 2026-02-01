# CLAUDE.md - Development Guide for ppget

This document provides information for AI assistants (like Claude) and developers working on the ppget project.

## Project Overview

**ppget** is a simple CLI tool for downloading PubMed articles. Unlike EDirect, it provides an intuitive interface with CSV/JSON output support.

- **Language**: Python 3.12+
- **Package Manager**: uv (primary) / pip (alternative)
- **Testing**: pytest (run with `uv run pytest`)
- **Linting**: ruff
- **Build**: hatchling
- **Distribution**: PyPI

## Project Structure

```
ppget/
├── ppget/              # Main package
│   ├── __init__.py     # Package initialization with version
│   ├── cli.py          # CLI argument parsing and main entry point
│   ├── search.py       # PubMed search functionality
│   ├── xml_extractor.py # XML parsing utilities
│   └── output.py       # CSV/JSON output handling
├── tests/              # Test suite
│   ├── __init__.py
│   ├── test_basic.py   # Core functionality tests
│   └── inspect_xml.py  # XML inspection utilities
├── main.py             # Alternative entry point for direct execution
├── pyproject.toml      # Project configuration and dependencies
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── README.md           # English documentation
└── README_ja.md        # Japanese documentation
```

## Core Components

### 1. XML Extraction (`ppget/xml_extractor.py`)

Handles extraction of text from PubMed XML elements. Key features:

- **`extract_abstract_from_xml()`**: Extracts abstract text with whitespace normalization
  - Replaces newlines with spaces
  - Normalizes multiple spaces to single space
  - Handles structured abstracts with labels (BACKGROUND, METHODS, etc.)
  - Preserves nested HTML tags content (italic, bold, etc.)

- **`extract_text_from_xml()`**: Generic XML text extraction utility

### 2. Search Functionality (`ppget/search.py`)

- Uses `pymed-paperscraper>=1.0.5` for PubMed API access
- Falls back to XML extraction for complex fields (abstract, title, journal)
- DOI extraction directly from pymed-paperscraper (no XML fallback needed since v1.0.5)
- Returns structured article data as list of dictionaries

### 3. CLI Interface (`ppget/cli.py`)

- Entry point: `main()` function
- Argument parsing with argparse
- Auto-detection of output format from file extension
- Validation of email and limit parameters

### 4. Output Handling (`ppget/output.py`)

- CSV output with metadata file (`.meta.txt`)
- JSON output with metadata
- Automatic filename generation with timestamp

## Development Setup

### 1. Install Dependencies

**This project uses uv as the primary package manager.**

```bash
# Install with development dependencies (recommended - uv)
uv pip install -e ".[dev]"

# Alternative with pip
pip install -e ".[dev]"
```

### 2. Install Pre-commit Hooks

```bash
uv pip install pre-commit
pre-commit install
```

This will automatically run:
- **ruff**: Linting and formatting
- **pytest**: All tests must pass before commit

### 3. Run Tests

**IMPORTANT: This project uses uv - always run tests with `uv run pytest`**

```bash
# Run all tests (recommended)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_basic.py

# Run specific test
uv run pytest tests/test_basic.py::TestXMLExtractor::test_extract_abstract_normalizes_whitespace
```

## Running the Application

### Method 1: Installed CLI

```bash
ppget "search query" -l 100 -f csv
```

### Method 2: Direct Execution

```bash
python main.py "search query" -l 100 -f csv
```

### Method 3: Module Execution

```bash
python -m ppget.cli "search query" -l 100 -f csv
```

## Testing Strategy

### Test Categories

1. **Validation Tests** (`TestValidation`)
   - Input parameter validation
   - Email format validation
   - Limit range checking

2. **Output Tests** (`TestOutput`)
   - File creation (CSV/JSON)
   - Path determination
   - Metadata generation

3. **XML Extraction Tests** (`TestXMLExtractor`)
   - Whitespace normalization
   - Newline handling
   - Structured abstract parsing
   - Edge cases (None, empty)

### Important: Abstract Whitespace Handling

As of v0.1.5, abstract extraction normalizes whitespace:
- Newlines (`\n`) are replaced with spaces
- Multiple consecutive spaces are reduced to single space
- Tabs and other whitespace are normalized

This ensures consistent output across different PubMed article formats.

## Release Process

### 1. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "0.1.5"  # Update this
```

### 2. Run Tests

```bash
uv run pytest
```

All tests must pass before release.

### 3. Commit and Tag

```bash
git add .
git commit -m "Release v0.1.5: Description of changes"
git tag -a v0.1.5 -m "Release v0.1.5"
git push origin main
git push origin v0.1.5
```

### 4. Build and Publish to PyPI

```bash
# Install build tools if needed
pip install build twine

# Build distribution packages
python -m build

# Upload to PyPI
twine upload dist/*
```

You'll need PyPI credentials (API token recommended).

## Code Style

- **Line length**: 100 characters
- **Python version**: 3.12+
- **Linter**: ruff
- **Type hints**: Used throughout (PEP 484)

## Common Tasks

### Add a new CLI option

1. Edit `ppget/cli.py` - add argument to parser
2. Update `search_pubmed()` or relevant function signature
3. Add tests in `tests/test_basic.py`
4. Update README.md and README_ja.md

### Add a new output format

1. Create handler function in `ppget/output.py`
2. Update `cli.py` to call new handler
3. Add format to choices in argparse
4. Add tests for new format
5. Update documentation

### Fix XML extraction issue

1. Edit `ppget/xml_extractor.py`
2. Add test case in `tests/test_basic.py::TestXMLExtractor`
3. Run tests to verify fix
4. Consider if `search.py` needs updates for fallback logic

## Dependencies

### Runtime
- `pymed-paperscraper>=1.0.5,<2.0.0`: PubMed API wrapper
  - v1.0.5+ correctly excludes reference DOIs, eliminating need for XML fallback

### Development
- `pytest>=7.0.0`: Testing framework
- `ruff>=0.1.0`: Linting and formatting

## Troubleshooting

### Tests failing with XML parsing errors

Check if the XML structure in test cases matches PubMed's actual structure. Use `tests/inspect_xml.py` to examine real PubMed XML.

### Pre-commit hook blocking commits

```bash
# Run hooks manually to see detailed errors
pre-commit run --all-files

# Fix linting issues automatically
ruff check --fix .
ruff format .
```

### PyPI upload fails

- Ensure version number is incremented
- Check PyPI credentials in `~/.pypirc` or use `--username __token__`
- Verify `dist/` contains only the latest build (remove old files)

## Contact

- **Issues**: https://github.com/masaki39/ppget/issues
- **Repository**: https://github.com/masaki39/ppget
- **Author**: masaki39

## License

MIT License - See LICENSE file for details.
