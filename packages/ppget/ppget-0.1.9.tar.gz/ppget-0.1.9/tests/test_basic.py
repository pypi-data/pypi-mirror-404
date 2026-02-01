"""
Basic tests for ppget functionality.

These tests verify core functionality without requiring actual PubMed API calls.
Run with: pytest
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from ppget.cli import validate_email, validate_limit
from ppget.output import determine_output_path, save_to_csv, save_to_json
from ppget.xml_extractor import (
    extract_abstract_from_xml,
    extract_text_from_xml,
    normalize_whitespace,
)


class TestValidation:
    """Test input validation functions."""

    def test_validate_limit_positive(self):
        """Valid limit should not raise error."""
        validate_limit(100)
        validate_limit(1)
        validate_limit(10000)

    def test_validate_limit_zero(self):
        """Zero limit should raise ValueError."""
        with pytest.raises(ValueError, match="positive number"):
            validate_limit(0)

    def test_validate_limit_negative(self):
        """Negative limit should raise ValueError."""
        with pytest.raises(ValueError, match="positive number"):
            validate_limit(-1)

    def test_validate_limit_too_large(self):
        """Limit over 10000 should raise ValueError."""
        with pytest.raises(ValueError, match="cannot exceed 10000"):
            validate_limit(10001)

    def test_validate_email_valid(self):
        """Valid email should not raise error."""
        validate_email("test@example.com")
        validate_email("user.name+tag@example.co.jp")
        validate_email("anonymous@example.com")  # Default

    def test_validate_email_invalid(self):
        """Invalid email should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("notanemail")
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("missing@domain")
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("@example.com")


class TestOutput:
    """Test output handling functions."""

    def test_save_to_json(self):
        """Test JSON file creation."""
        test_data = [{"pubmed_id": "12345", "title": "Test Article", "abstract": "Test abstract"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            save_to_json(test_data, output_path)

            assert output_path.exists()
            with open(output_path, encoding="utf-8") as f:
                loaded_data = json.load(f)
                assert loaded_data == test_data

    def test_save_to_json_empty_data(self):
        """Empty data should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            with pytest.raises(ValueError, match="No data to save"):
                save_to_json([], output_path)

    def test_save_to_csv(self):
        """Test CSV file creation including PubMed link column."""
        test_data = [
            {
                "pubmed_id": "12345",
                "title": "Test Article",
                "abstract": "Test abstract",
                "journal": "Test Journal",
                "publication_date": "2024-01-01",
                "doi": "10.1234/test",
                "authors": [{"firstname": "John", "lastname": "Doe"}],
                "keywords": ["test", "article"],
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            save_to_csv(test_data, output_path)

            assert output_path.exists()
            with open(output_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["pubmed_id"] == "12345"
                assert rows[0]["pubmed_link"] == "https://pubmed.ncbi.nlm.nih.gov/12345"
                assert rows[0]["title"] == "Test Article"
                assert rows[0]["authors"] == "John Doe"
                assert rows[0]["keywords"] == "test; article"

    def test_save_to_csv_without_pubmed_id(self):
        """Missing PubMed ID should produce empty ID/link fields."""
        test_data = [
            {
                "title": "No ID Article",
                "authors": [],
                "keywords": [],
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_no_id.csv"
            save_to_csv(test_data, output_path)

            with open(output_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row = next(reader)
                assert row["pubmed_id"] == ""
                assert row["pubmed_link"] == ""

    def test_save_to_csv_empty_data(self):
        """Empty data should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            with pytest.raises(ValueError, match="No data to save"):
                save_to_csv([], output_path)

    def test_determine_output_path_default(self):
        """Test default output path generation."""
        path = determine_output_path(None, "csv")
        assert path.suffix == ".csv"
        assert "pubmed_" in path.name

    def test_determine_output_path_with_file(self):
        """Test custom file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = f"{tmpdir}/custom.csv"
            path = determine_output_path(custom_path, "csv")
            assert str(path) == custom_path


class TestWhitespaceNormalization:
    """Test whitespace normalization function."""

    def test_normalize_whitespace_none(self):
        """None input should return None."""
        assert normalize_whitespace(None) is None

    def test_normalize_whitespace_empty(self):
        """Empty string should return None."""
        assert normalize_whitespace("") is None
        assert normalize_whitespace("   ") is None

    def test_normalize_whitespace_newlines(self):
        """Newlines should be replaced with spaces."""
        text = "Line one\nLine two\nLine three"
        result = normalize_whitespace(text)
        assert result == "Line one Line two Line three"
        assert "\n" not in result

    def test_normalize_whitespace_multiple_spaces(self):
        """Multiple spaces should be collapsed to single space."""
        text = "Word1  Word2   Word3    Word4"
        result = normalize_whitespace(text)
        assert result == "Word1 Word2 Word3 Word4"
        assert "  " not in result

    def test_normalize_whitespace_tabs(self):
        """Tabs should be replaced with spaces."""
        text = "Word1\tWord2\t\tWord3"
        result = normalize_whitespace(text)
        assert result == "Word1 Word2 Word3"
        assert "\t" not in result

    def test_normalize_whitespace_mixed(self):
        """Mixed whitespace should be normalized."""
        text = "Word1\n  Word2\t\nWord3   \n\nWord4"
        result = normalize_whitespace(text)
        assert result == "Word1 Word2 Word3 Word4"

    def test_normalize_whitespace_leading_trailing(self):
        """Leading and trailing whitespace should be stripped."""
        text = "  \n\tText with spaces\t\n  "
        result = normalize_whitespace(text)
        assert result == "Text with spaces"


class TestXMLExtractor:
    """Test XML extraction utilities."""

    def test_extract_text_from_xml_none(self):
        """None XML element should return None."""
        result = extract_text_from_xml(None, ".//test")
        assert result is None

    def test_extract_abstract_from_xml_none(self):
        """None XML element should return None."""
        result = extract_abstract_from_xml(None)
        assert result is None

    def test_extract_abstract_normalizes_whitespace(self):
        """Abstract extraction should normalize whitespace."""
        from xml.etree import ElementTree as ET

        # Test case 1: Multiple spaces
        xml_str = """
        <PubmedArticle>
            <AbstractText>This  has   multiple    spaces.</AbstractText>
        </PubmedArticle>
        """
        xml = ET.fromstring(xml_str)
        result = extract_abstract_from_xml(xml)
        assert result == "This has multiple spaces."

    def test_extract_abstract_replaces_newlines_with_spaces(self):
        """Abstract extraction should replace newlines with spaces."""
        from xml.etree import ElementTree as ET

        # Test case: Newlines in text
        xml_str = """
        <PubmedArticle>
            <AbstractText>Line one
Line two
Line three.</AbstractText>
        </PubmedArticle>
        """
        xml = ET.fromstring(xml_str)
        result = extract_abstract_from_xml(xml)
        assert result == "Line one Line two Line three."
        assert "\n" not in result

    def test_extract_abstract_structured_with_labels(self):
        """Structured abstract with labels should be space-separated."""
        from xml.etree import ElementTree as ET

        xml_str = """
        <PubmedArticle>
            <AbstractText Label="BACKGROUND">This is
background.</AbstractText>
            <AbstractText Label="METHODS">These are methods.</AbstractText>
        </PubmedArticle>
        """
        xml = ET.fromstring(xml_str)
        result = extract_abstract_from_xml(xml)
        assert result == "BACKGROUND: This is background. METHODS: These are methods."
        assert "\n" not in result

    def test_extract_abstract_mixed_whitespace(self):
        """Abstract with tabs and newlines should be normalized."""
        from xml.etree import ElementTree as ET

        xml_str = """
        <PubmedArticle>
            <AbstractText>Word1	Word2
Word3   Word4</AbstractText>
        </PubmedArticle>
        """
        xml = ET.fromstring(xml_str)
        result = extract_abstract_from_xml(xml)
        assert result == "Word1 Word2 Word3 Word4"
        assert "\n" not in result
        assert "\t" not in result
        # Verify no multiple spaces
        assert "  " not in result
