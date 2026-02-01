"""
Tests for src/symderive/data/io.py - Import and Export functions.
"""

import json
import pytest
import polars as pl

from symderive.data.io import Import, Export


# =============================================================================
# CSV Import/Export Tests
# =============================================================================


class TestCSVImport:
    """Tests for CSV Import functionality."""

    def test_import_csv_basic(self, tmp_path):
        """Import a CSV file and verify data structure."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA")

        result = Import(str(csv_file))

        assert isinstance(result, pl.DataFrame)
        assert result.shape == (2, 3)
        assert result.columns == ["name", "age", "city"]
        assert result["name"].to_list() == ["Alice", "Bob"]
        assert result["age"].to_list() == [30, 25]

    def test_import_csv_with_format_override(self, tmp_path):
        """Import file with explicit format specification."""
        data_file = tmp_path / "data.txt"
        data_file.write_text("a,b\n1,2\n3,4")

        result = Import(str(data_file), format="CSV")

        assert isinstance(result, pl.DataFrame)
        assert result.shape == (2, 2)


class TestCSVExport:
    """Tests for CSV Export functionality."""

    def test_export_csv_dataframe(self, tmp_path):
        """Export a Polars DataFrame to CSV."""
        csv_file = tmp_path / "output.csv"
        df = pl.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

        result = Export(str(csv_file), df)

        assert result == csv_file
        assert csv_file.exists()

    def test_csv_roundtrip(self, tmp_path):
        """Export data to CSV, reimport and verify roundtrip."""
        csv_file = tmp_path / "roundtrip.csv"
        original_df = pl.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95, 87, 92],
        })

        Export(str(csv_file), original_df)
        reimported = Import(str(csv_file))

        assert reimported.shape == original_df.shape
        assert reimported.columns == original_df.columns
        assert reimported["name"].to_list() == original_df["name"].to_list()
        assert reimported["score"].to_list() == original_df["score"].to_list()

    def test_export_csv_from_dict(self, tmp_path):
        """Export a dict to CSV (auto-converts to DataFrame)."""
        csv_file = tmp_path / "dict_export.csv"
        data = {"col1": [1, 2], "col2": [3, 4]}

        Export(str(csv_file), data)
        result = Import(str(csv_file))

        assert result.shape == (2, 2)


# =============================================================================
# JSON Import/Export Tests
# =============================================================================


class TestJSONImport:
    """Tests for JSON Import functionality."""

    def test_import_json_dict(self, tmp_path):
        """Import a JSON file containing a dict."""
        json_file = tmp_path / "config.json"
        json_file.write_text('{"key": "value", "number": 42}')

        result = Import(str(json_file))

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_import_json_list(self, tmp_path):
        """Import a JSON file containing a list."""
        json_file = tmp_path / "items.json"
        json_file.write_text('[1, 2, 3, "four"]')

        result = Import(str(json_file))

        assert isinstance(result, list)
        assert result == [1, 2, 3, "four"]


class TestJSONExport:
    """Tests for JSON Export functionality."""

    def test_export_json_dict(self, tmp_path):
        """Export a dict to JSON and verify."""
        json_file = tmp_path / "output.json"
        data = {"a": 1, "b": [2, 3], "c": {"nested": True}}

        result = Export(str(json_file), data)

        assert result == json_file
        assert json_file.exists()

        with open(json_file) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_json_roundtrip(self, tmp_path):
        """Export to JSON and reimport to verify roundtrip."""
        json_file = tmp_path / "roundtrip.json"
        original = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ],
            "count": 2,
        }

        Export(str(json_file), original)
        reimported = Import(str(json_file))

        assert reimported == original


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in Import/Export."""

    def test_import_nonexistent_file(self):
        """Import nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Import("/nonexistent/path/to/file.csv")

    def test_import_wrong_format_csv_as_json(self, tmp_path):
        """Import with wrong format specified raises error."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2")

        with pytest.raises(json.JSONDecodeError):
            Import(str(csv_file), format="JSON")

    def test_import_unknown_format(self, tmp_path):
        """Import with unknown format raises ValueError."""
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("hello")

        with pytest.raises(ValueError, match="Unknown format"):
            Import(str(txt_file), format="INVALID_FORMAT")

    def test_export_unknown_format(self, tmp_path):
        """Export with unknown format raises ValueError."""
        out_file = tmp_path / "output.txt"

        with pytest.raises(ValueError, match="Unknown format"):
            Export(str(out_file), {"data": 1}, format="INVALID_FORMAT")

    def test_export_to_invalid_path(self, tmp_path):
        """Export to invalid path raises error."""
        invalid_path = "/nonexistent/directory/file.csv"
        df = pl.DataFrame({"a": [1]})

        with pytest.raises((FileNotFoundError, OSError)):
            Export(invalid_path, df)

    def test_export_pdf_requires_figure(self, tmp_path):
        """PDF export without matplotlib figure raises ValueError."""
        pdf_file = tmp_path / "output.pdf"

        with pytest.raises(ValueError, match="PDF export requires a matplotlib figure"):
            Export(str(pdf_file), {"not": "a figure"})


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in Import/Export."""

    def test_import_empty_csv(self, tmp_path):
        """Import empty CSV file with headers only."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("col1,col2,col3\n")

        result = Import(str(csv_file))

        assert isinstance(result, pl.DataFrame)
        assert result.shape == (0, 3)
        assert result.columns == ["col1", "col2", "col3"]

    def test_import_empty_json_object(self, tmp_path):
        """Import empty JSON object."""
        json_file = tmp_path / "empty.json"
        json_file.write_text("{}")

        result = Import(str(json_file))

        assert result == {}

    def test_import_empty_json_array(self, tmp_path):
        """Import empty JSON array."""
        json_file = tmp_path / "empty_array.json"
        json_file.write_text("[]")

        result = Import(str(json_file))

        assert result == []

    def test_import_empty_text_file(self, tmp_path):
        """Import empty text file."""
        txt_file = tmp_path / "empty.txt"
        txt_file.write_text("")

        result = Import(str(txt_file))

        assert result == ""

    def test_unicode_csv(self, tmp_path):
        """Import and export CSV with unicode content."""
        csv_file = tmp_path / "unicode.csv"
        csv_file.write_text("name,greeting\nAlice,Hello\nBob,Bonjour")

        result = Import(str(csv_file))

        assert result["greeting"].to_list() == ["Hello", "Bonjour"]

    def test_unicode_json(self, tmp_path):
        """Import and export JSON with unicode content."""
        json_file = tmp_path / "unicode.json"
        original = {"greeting": "Hello", "name": "Alice"}

        Export(str(json_file), original)
        result = Import(str(json_file))

        assert result == original

    def test_unicode_text(self, tmp_path):
        """Import and export text file with unicode content."""
        txt_file = tmp_path / "unicode.txt"
        content = "Hello World - Plain ASCII text"

        Export(str(txt_file), content)
        result = Import(str(txt_file))

        assert result == content


# =============================================================================
# TSV and Parquet Tests
# =============================================================================


class TestTSVImportExport:
    """Tests for TSV Import/Export functionality."""

    def test_tsv_roundtrip(self, tmp_path):
        """Export to TSV and reimport to verify roundtrip."""
        tsv_file = tmp_path / "data.tsv"
        original = pl.DataFrame({"a": [1, 2], "b": [3, 4]})

        Export(str(tsv_file), original)
        result = Import(str(tsv_file))

        assert result.shape == original.shape
        assert result["a"].to_list() == original["a"].to_list()


class TestParquetImportExport:
    """Tests for Parquet Import/Export functionality."""

    def test_parquet_roundtrip(self, tmp_path):
        """Export to Parquet and reimport to verify roundtrip."""
        parquet_file = tmp_path / "data.parquet"
        original = pl.DataFrame({"x": [10, 20, 30], "y": ["a", "b", "c"]})

        Export(str(parquet_file), original)
        result = Import(str(parquet_file))

        assert result.shape == original.shape
        assert result["x"].to_list() == original["x"].to_list()
        assert result["y"].to_list() == original["y"].to_list()


# =============================================================================
# Text Import/Export Tests
# =============================================================================


class TestTextImportExport:
    """Tests for Text Import/Export functionality."""

    def test_text_import(self, tmp_path):
        """Import a text file."""
        txt_file = tmp_path / "readme.txt"
        content = "This is line 1\nThis is line 2"
        txt_file.write_text(content)

        result = Import(str(txt_file))

        assert result == content

    def test_text_export(self, tmp_path):
        """Export text content to file."""
        txt_file = tmp_path / "output.txt"
        content = "Hello, World!"

        Export(str(txt_file), content)

        assert txt_file.read_text() == content

    def test_text_format_fallback(self, tmp_path):
        """Unknown extension falls back to text format."""
        unknown_file = tmp_path / "data.xyz"
        unknown_file.write_text("some content")

        result = Import(str(unknown_file))

        assert result == "some content"
