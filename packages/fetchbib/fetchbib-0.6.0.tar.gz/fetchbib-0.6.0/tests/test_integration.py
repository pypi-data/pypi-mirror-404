"""Integration tests that hit live APIs.

Skipped by default. Run with:
    pytest -m integration
"""

import tempfile

import pytest

from conftest import AUTHOR_A, DOI_A, SEARCH_QUERY_A
from fetchbib.formatter import format_bibtex
from fetchbib.resolver import resolve_doi, search_openalex

pytestmark = pytest.mark.integration


class TestLiveResolution:
    """End-to-end tests against doi.org and OpenAlex."""

    def test_doi_resolution(self):
        raw = resolve_doi(DOI_A)
        result = format_bibtex(raw)
        assert AUTHOR_A in result
        assert "2024" in result

    def test_free_text_search(self):
        dois = search_openalex(SEARCH_QUERY_A)
        raw = resolve_doi(dois[0])
        result = format_bibtex(raw)
        assert AUTHOR_A in result

    def test_file_input_via_cli(self):
        """Resolve a DOI through the full CLI path."""
        import sys
        from io import StringIO
        from unittest.mock import patch

        from fetchbib.cli import main

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{DOI_A}\n")
            f.flush()
            path = f.name

        old_argv = sys.argv
        sys.argv = ["fbib", "--file", path]
        stdout_capture = StringIO()

        try:
            with patch("sys.stdout", stdout_capture):
                main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        output = stdout_capture.getvalue()
        assert AUTHOR_A in output
