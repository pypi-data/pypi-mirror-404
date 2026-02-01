"""
PubMed search functionality.

This module handles searching PubMed and extracting article data,
with XML fallback for fields that may have parsing issues.
"""

from pymed_paperscraper import PubMed

from .xml_extractor import (
    extract_abstract_from_xml,
    extract_text_from_xml,
    normalize_whitespace,
)


def search_pubmed(
    query: str, max_results: int = 100, email: str = "anonymous@example.com", quiet: bool = False
) -> list[dict]:
    """
    Search PubMed and retrieve article data.

    This function uses pymed-paperscraper for the initial data extraction,
    with XML fallback for fields that may contain nested HTML tags or
    have other parsing issues.

    Args:
        query: Search query
        max_results: Maximum number of results to retrieve
        email: Email address (for API rate limit relaxation)
        quiet: If True, suppress progress messages

    Returns:
        List of article data dictionaries

    Raises:
        RuntimeError: If PubMed query fails
        ValueError: If query is empty or invalid
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    pubmed = PubMed(tool="ppget", email=email)

    try:
        results = pubmed.query(query, max_results=max_results)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        # Provide more specific error messages for common issues
        if 'timeout' in error_msg or 'timed out' in error_msg:
            raise RuntimeError(
                "PubMed query timed out. Try reducing --limit or check your network connection."
            ) from e
        elif 'connection' in error_msg or 'network' in error_msg:
            raise RuntimeError(
                f"Network error while querying PubMed: {e}"
            ) from e
        else:
            raise RuntimeError(f"PubMed query failed: {e}") from e

    articles = []
    for idx, article in enumerate(results, 1):
        xml_element = getattr(article, "xml", None)

        # Extract all fields from pymed-paperscraper first
        title = getattr(article, "title", None)
        abstract = getattr(article, "abstract", None)
        journal = getattr(article, "journal", None)
        doi_raw = getattr(article, "doi", None)

        # XML fallback for fields that may have nested HTML tags
        # This ensures we don't lose data due to pymed-paperscraper's parsing limitations
        if xml_element is not None:
            # Title: May contain italic tags for species names, etc.
            if not title:
                title = extract_text_from_xml(xml_element, ".//ArticleTitle")

            # Abstract: Handles structured abstracts and nested tags
            if not abstract:
                abstract = extract_abstract_from_xml(xml_element)
            else:
                # Normalize pymed-extracted abstract to ensure consistent formatting
                # (XML extraction already normalizes, pymed extraction doesn't)
                abstract = normalize_whitespace(abstract)

            # Journal: Usually simple text, but check just in case
            if not journal:
                journal = extract_text_from_xml(xml_element, ".//Journal/Title")

        # Use DOI directly from pymed-paperscraper
        # As of pymed-paperscraper 1.0.5, DOI extraction correctly excludes reference DOIs
        # Normalize by taking first line only (some DOIs contain newlines)
        doi = doi_raw.split('\n')[0].strip() if doi_raw else None

        # Build article data dictionary
        article_data = {
            "pubmed_id": getattr(article, "pubmed_id", None),
            "title": title,
            "abstract": abstract,
            "keywords": getattr(article, "keywords", None) or [],
            "journal": journal,
            "publication_date": (
                str(article.publication_date)
                if getattr(article, "publication_date", None)
                else None
            ),
            "authors": [
                {"firstname": author.get("firstname"), "lastname": author.get("lastname")}
                for author in (getattr(article, "authors", None) or [])
            ],
            "doi": doi,
        }
        articles.append(article_data)

        # Show progress for large queries (every 100 articles)
        if not quiet and idx % 100 == 0:
            print(f"  Retrieved {idx} articles...", flush=True)

    return articles
