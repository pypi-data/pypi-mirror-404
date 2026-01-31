"""Tests for the resolver (Phase 2).

All HTTP calls are mocked — no network access needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from conftest import DOI_A, RAW_BIBTEX_A, SEARCH_QUERY_A
from fetchbib.resolver import (
    ResolverError,
    extract_arxiv_id,
    is_arxiv_doi,
    is_doi,
    normalize_doi_input,
    resolve_arxiv,
    resolve_doi,
    resolve_to_bibtex,
    search_openalex,
)

# ---------------------------------------------------------------------------
# is_doi
# ---------------------------------------------------------------------------


class TestIsDoi:
    """Tests for DOI pattern matching."""

    @pytest.mark.parametrize(
        "value",
        [
            "10.2196/jmir.1933",
            "10.1000/xyz123",
            "10.1234/some-thing_(here)",
        ],
    )
    def test_valid_dois(self, value):
        assert is_doi(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "not a doi",
            "10.12345",  # no suffix after slash
            "",
            "http://doi.org/10.2196/jmir.1933",  # full URL
        ],
    )
    def test_invalid_inputs(self, value):
        assert is_doi(value) is False


# ---------------------------------------------------------------------------
# is_arxiv_doi
# ---------------------------------------------------------------------------


class TestIsArxivDoi:
    """Tests for arXiv DOI detection."""

    @pytest.mark.parametrize(
        "value",
        [
            "10.48550/arXiv.2410.21554",
            "10.48550/arxiv.2410.21554",  # lowercase
            "10.48550/ARXIV.2410.21554",  # uppercase
            "10.48550/arXiv.1234.56789",
            "10.48550/arXiv.hep-ph/0307015",
        ],
    )
    def test_valid_arxiv_dois(self, value):
        assert is_arxiv_doi(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "10.2196/jmir.1933",  # regular DOI
            "10.1073/pnas.2322823121",  # PNAS DOI
            "10.48550/other.1234",  # different prefix after 10.48550
            "",
        ],
    )
    def test_non_arxiv_dois(self, value):
        assert is_arxiv_doi(value) is False


# ---------------------------------------------------------------------------
# extract_arxiv_id
# ---------------------------------------------------------------------------


class TestExtractArxivId:
    """Tests for extracting arXiv ID from DOI."""

    @pytest.mark.parametrize(
        "doi,expected",
        [
            ("10.48550/arXiv.2410.21554", "2410.21554"),
            ("10.48550/arXiv.1234.56789", "1234.56789"),
            ("10.48550/arXiv.hep-ph/0307015", "hep-ph/0307015"),
        ],
    )
    def test_extracts_arxiv_id(self, doi, expected):
        assert extract_arxiv_id(doi) == expected


# ---------------------------------------------------------------------------
# resolve_arxiv
# ---------------------------------------------------------------------------


class TestResolveArxiv:
    """Tests for fetching BibTeX from arXiv."""

    @patch("fetchbib.resolver.requests.get")
    def test_returns_bibtex_on_success(self, mock_get):
        bibtex = "@misc{deverna2024, author={DeVerna}, year={2024}}"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = bibtex.encode("utf-8")
        mock_get.return_value = mock_resp

        result = resolve_arxiv("2410.21554")

        assert result == bibtex
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "arxiv.org/bibtex/2410.21554" in call_args[0][0]

    @patch("fetchbib.resolver.requests.get")
    def test_utf8_encoding_preserved(self, mock_get):
        """UTF-8 characters in author names are correctly decoded."""
        bibtex = "@misc{key, author={Müller, Hans}, year={2024}}"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = bibtex.encode("utf-8")
        mock_get.return_value = mock_resp

        result = resolve_arxiv("2410.21554")

        assert "Müller" in result

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_http_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="arXiv resolution failed.*404"):
            resolve_arxiv("9999.99999")


# ---------------------------------------------------------------------------
# normalize_doi_input
# ---------------------------------------------------------------------------


class TestNormalizeDOIInput:
    """Tests for stripping DOI URL prefixes."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
            ("http://doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
            ("https://dx.doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
            ("http://dx.doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
        ],
    )
    def test_strips_doi_url_prefixes(self, url, expected):
        assert normalize_doi_input(url) == expected

    def test_bare_doi_unchanged(self):
        assert normalize_doi_input("10.2196/jmir.1933") == "10.2196/jmir.1933"

    def test_non_doi_string_unchanged(self):
        assert normalize_doi_input(SEARCH_QUERY_A) == SEARCH_QUERY_A


# ---------------------------------------------------------------------------
# resolve_doi
# ---------------------------------------------------------------------------


class TestResolveDoi:
    """Tests for fetching BibTeX from doi.org."""

    @patch("fetchbib.resolver.requests.get")
    def test_returns_bibtex_on_success(self, mock_get):
        bibtex = "@article{Key, author={Someone}, year={2020}}"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = bibtex.encode("utf-8")
        mock_get.return_value = mock_resp

        result = resolve_doi("10.1234/test")

        assert result == bibtex
        # Verify correct headers were sent
        call_kwargs = mock_get.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers["Accept"] == "text/bibliography; style=bibtex"
        assert "fetchbib" in headers["User-Agent"]

    @patch("fetchbib.resolver.requests.get")
    def test_utf8_encoding_preserved(self, mock_get):
        """UTF-8 characters in author names are correctly decoded."""
        bibtex = "@article{Key, author={Meskó, Bertalan}, year={2023}}"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = bibtex.encode("utf-8")
        mock_get.return_value = mock_resp

        result = resolve_doi("10.1234/test")

        assert "Meskó" in result
        assert "MeskÃ³" not in result  # This would appear with wrong encoding

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_http_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="404"):
            resolve_doi("10.1234/missing")


# ---------------------------------------------------------------------------
# search_openalex
# ---------------------------------------------------------------------------


class TestSearchOpenalex:
    """Tests for the OpenAlex search API."""

    @patch("fetchbib.resolver.requests.get")
    def test_returns_list_of_dois(self, mock_get, monkeypatch):
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"doi": f"https://doi.org/{DOI_A}"},
                {"doi": "https://doi.org/10.9999/other"},
            ]
        }
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        result = search_openalex(SEARCH_QUERY_A)
        assert result == [DOI_A]

    @patch("fetchbib.resolver.requests.get")
    def test_max_results_parameter(self, mock_get, monkeypatch):
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"doi": f"https://doi.org/{DOI_A}"},
                {"doi": "https://doi.org/10.9999/second"},
                {"doi": "https://doi.org/10.9999/third"},
            ]
        }
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        result = search_openalex(SEARCH_QUERY_A, max_results=3)
        assert result == [DOI_A, "10.9999/second", "10.9999/third"]
        # Verify per_page parameter was passed
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params["per_page"] == 3

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_empty_results(self, mock_get, monkeypatch):
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="[Nn]o results"):
            search_openalex("nonexistent gibberish query")

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_http_failure(self, mock_get, monkeypatch):
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="503"):
            search_openalex("anything")

    @patch("fetchbib.resolver.requests.get")
    def test_includes_api_key_from_env(self, mock_get, monkeypatch):
        """API key from env var is included in request."""
        monkeypatch.setenv("OPENALEX_API_KEY", "test_key_env")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"doi": f"https://doi.org/{DOI_A}"}]}
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        search_openalex("test query")

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params["api_key"] == "test_key_env"

    @patch("fetchbib.resolver.requests.get")
    def test_includes_api_key_from_config(self, mock_get, tmp_path, monkeypatch):
        """API key from config file is included when env var not set."""
        import json

        from fetchbib import config

        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"openalex_api_key": "test_key_config"}))
        monkeypatch.setattr(config, "CONFIG_FILE", config_file)
        monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"doi": f"https://doi.org/{DOI_A}"}]}
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        search_openalex("test query")

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params["api_key"] == "test_key_config"

    @patch("fetchbib.resolver.requests.get")
    @patch("fetchbib.resolver.config.get_openalex_api_key", return_value=None)
    def test_warning_when_no_api_key(self, mock_config, mock_get, monkeypatch, capsys):
        """Warning is shown to stderr when no API key is configured."""
        from fetchbib.resolver import _warn_no_api_key_once

        if hasattr(_warn_no_api_key_once, "_shown"):
            monkeypatch.delattr(_warn_no_api_key_once, "_shown")
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"doi": f"https://doi.org/{DOI_A}"}]}
        mock_resp.headers = {"X-RateLimit-Remaining": "95"}
        mock_get.return_value = mock_resp

        search_openalex("test query")

        captured = capsys.readouterr()
        assert "API key" in captured.err or "api key" in captured.err.lower()
        assert "95" in captured.err

    @patch("fetchbib.resolver.requests.get")
    @patch("fetchbib.resolver.config.get_openalex_api_key", return_value=None)
    def test_warning_shown_only_once(self, mock_config, mock_get, monkeypatch, capsys):
        """Warning is shown only once per session, not on every call."""
        from fetchbib.resolver import _warn_no_api_key_once

        if hasattr(_warn_no_api_key_once, "_shown"):
            monkeypatch.delattr(_warn_no_api_key_once, "_shown")
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"doi": f"https://doi.org/{DOI_A}"}]}
        mock_resp.headers = {"X-RateLimit-Remaining": "95"}
        mock_get.return_value = mock_resp

        search_openalex("first query")
        search_openalex("second query")

        captured = capsys.readouterr()
        # Warning should appear exactly once
        assert captured.err.count("No OpenAlex API key configured") == 1

    @patch("fetchbib.resolver.requests.get")
    def test_no_warning_when_api_key_set(self, mock_get, monkeypatch, capsys):
        """No warning is shown when API key is configured."""
        monkeypatch.setenv("OPENALEX_API_KEY", "my_key")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"doi": f"https://doi.org/{DOI_A}"}]}
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        search_openalex("test query")

        captured = capsys.readouterr()
        assert "API key" not in captured.err

    @patch("fetchbib.resolver.requests.get")
    def test_skips_results_without_doi(self, mock_get, monkeypatch):
        """Results without a DOI are skipped."""
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"doi": None, "display_name": "No DOI paper"},
                {"doi": f"https://doi.org/{DOI_A}"},
            ]
        }
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        result = search_openalex("test query", max_results=2)
        assert result == [DOI_A]

    @patch("fetchbib.resolver.requests.get")
    def test_raises_when_results_exist_but_none_have_dois(self, mock_get, monkeypatch):
        """Distinct error when results exist but none have DOIs."""
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"doi": None, "display_name": "Paper without DOI"},
                {"doi": None, "display_name": "Another paper without DOI"},
            ]
        }
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="No results with DOIs found"):
            search_openalex("query with no doi results")


# ---------------------------------------------------------------------------
# Config / User-Agent
# ---------------------------------------------------------------------------


class TestApiKeyConfig:
    """Tests for OpenAlex API key configuration."""

    def test_get_api_key_returns_config_file_when_env_unset(
        self, tmp_path, monkeypatch
    ):
        """Config file is used when env var is not set."""
        import json

        from fetchbib import config

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"openalex_api_key": "config_key_456"}))
        monkeypatch.setattr(config, "CONFIG_FILE", config_file)
        monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)

        result = config.get_openalex_api_key()
        assert result == "config_key_456"

    def test_get_api_key_returns_none_when_neither_set(self, tmp_path, monkeypatch):
        """Returns None when neither env var nor config file has a key."""
        from fetchbib import config

        config_file = tmp_path / "config.json"
        monkeypatch.setattr(config, "CONFIG_FILE", config_file)
        monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)

        result = config.get_openalex_api_key()
        assert result is None

    def test_env_var_takes_precedence_over_config_file(self, tmp_path, monkeypatch):
        """Env var wins even when config file has a different key."""
        import json

        from fetchbib import config

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"openalex_api_key": "config_key"}))
        monkeypatch.setattr(config, "CONFIG_FILE", config_file)
        monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
        monkeypatch.setenv("OPENALEX_API_KEY", "env_key")

        result = config.get_openalex_api_key()
        assert result == "env_key"

    def test_set_api_key_saves_to_config_file(self, tmp_path, monkeypatch):
        """set_openalex_api_key persists to config file."""
        import json

        from fetchbib import config

        config_file = tmp_path / "config.json"
        monkeypatch.setattr(config, "CONFIG_FILE", config_file)
        monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)

        config.set_openalex_api_key("my_new_key_789")

        saved = json.loads(config_file.read_text())
        assert saved["openalex_api_key"] == "my_new_key_789"


# ---------------------------------------------------------------------------
# resolve_to_bibtex
# ---------------------------------------------------------------------------


class TestResolveToBibtex:
    """Tests for the resolve_to_bibtex orchestrator."""

    @pytest.mark.parametrize(
        "query",
        ["10.2196/jmir.1933", "https://doi.org/10.2196/jmir.1933"],
    )
    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_routes_doi_directly(self, mock_search, mock_resolve_doi, query):
        """DOIs (bare or URL form) route directly to resolve_doi."""
        mock_resolve_doi.return_value = RAW_BIBTEX_A

        result = resolve_to_bibtex(query)

        mock_resolve_doi.assert_called_once_with("10.2196/jmir.1933")
        mock_search.assert_not_called()
        assert len(result) == 1
        assert "@article{Key1," in result[0]

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_routes_non_doi_through_search(self, mock_search, mock_resolve_doi):
        mock_search.return_value = [DOI_A]
        mock_resolve_doi.return_value = RAW_BIBTEX_A

        result = resolve_to_bibtex(SEARCH_QUERY_A)

        mock_search.assert_called_once_with(SEARCH_QUERY_A, 1)
        mock_resolve_doi.assert_called_once_with(DOI_A)
        assert len(result) == 1

    @patch("fetchbib.resolver.resolve_arxiv")
    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_routes_arxiv_doi_to_arxiv(self, mock_search, mock_resolve_doi, mock_arxiv):
        mock_arxiv.return_value = "@misc{deverna2024,author={DeVerna},year={2024}}"

        result = resolve_to_bibtex("10.48550/arXiv.2410.21554")

        mock_arxiv.assert_called_once_with("2410.21554")
        mock_resolve_doi.assert_not_called()
        mock_search.assert_not_called()
        assert len(result) == 1

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_applies_protect_titles(self, mock_search, mock_resolve_doi):
        mock_resolve_doi.return_value = (
            "@article{Key,title={A {GPU} Test},author={Smith}}"
        )

        result = resolve_to_bibtex("10.1234/test", protect_titles=True)

        assert "title = {{A GPU Test}}" in result[0]

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_applies_exclude_issn(self, mock_search, mock_resolve_doi):
        mock_resolve_doi.return_value = "@article{Key,title={Test},issn={1234-5678}}"

        result = resolve_to_bibtex("10.1234/test", exclude_issn=True)

        assert "issn" not in result[0].lower()

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_applies_exclude_doi(self, mock_search, mock_resolve_doi):
        mock_resolve_doi.return_value = "@article{Key,title={Test},doi={10.1234/ex}}"

        result = resolve_to_bibtex("10.1234/test", exclude_doi=True)

        assert "doi" not in result[0].lower()

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_returns_multiple_results_for_search(self, mock_search, mock_resolve_doi):
        mock_search.return_value = [DOI_A, "10.9999/second"]
        mock_resolve_doi.side_effect = [
            "@article{Key1,author={Alice}}",
            "@article{Key2,author={Bob}}",
        ]

        result = resolve_to_bibtex(SEARCH_QUERY_A, max_results=2)

        assert len(result) == 2
        mock_search.assert_called_once_with(SEARCH_QUERY_A, 2)

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_partial_failure_continues(self, mock_search, mock_resolve_doi, capsys):
        """When one DOI fails during search results, others still return."""
        mock_search.return_value = [DOI_A, "10.9999/broken"]
        mock_resolve_doi.side_effect = [
            "@article{Key1,author={Alice}}",
            ResolverError("HTTP 500"),
        ]

        result = resolve_to_bibtex(SEARCH_QUERY_A, max_results=2)

        assert len(result) == 1
        assert "Key1" in result[0]
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "10.9999/broken" in captured.err

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_invalid_bibtex_response_continues(
        self, mock_search, mock_resolve_doi, capsys
    ):
        """When a DOI returns HTML instead of BibTeX, warn and continue."""
        mock_search.return_value = ["10.5281/zenodo.123", DOI_A]
        mock_resolve_doi.side_effect = [
            "<!DOCTYPE html><html>...</html>",  # HTML instead of BibTeX
            "@article{Key1,author={Alice}}",
        ]

        result = resolve_to_bibtex(SEARCH_QUERY_A, max_results=2)

        assert len(result) == 1
        assert "Key1" in result[0]
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "10.5281/zenodo.123" in captured.err

    @patch("fetchbib.resolver.resolve_doi")
    def test_invalid_bibtex_for_direct_doi_raises(self, mock_resolve_doi):
        """When a direct DOI returns invalid BibTeX, raise ResolverError."""
        mock_resolve_doi.return_value = "<!DOCTYPE html><html>...</html>"

        with pytest.raises(ResolverError, match="Invalid BibTeX response"):
            resolve_to_bibtex("10.5281/zenodo.123")

    @patch("fetchbib.resolver.resolve_arxiv")
    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_arxiv_dois_in_search_results_routed_correctly(
        self, mock_search, mock_resolve_doi, mock_arxiv
    ):
        """arXiv DOIs from search results are routed to resolve_arxiv."""
        mock_search.return_value = ["10.48550/arxiv.2410.21554"]
        mock_arxiv.return_value = "@misc{key,author={Someone},year={2024}}"

        result = resolve_to_bibtex(SEARCH_QUERY_A)

        mock_arxiv.assert_called_once_with("2410.21554")
        mock_resolve_doi.assert_not_called()
        assert len(result) == 1

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_openalex")
    def test_all_search_results_fail_raises_error(self, mock_search, mock_resolve_doi):
        """When all search results fail to resolve, raise ResolverError."""
        mock_search.return_value = ["10.5281/zenodo.123", "10.5281/zenodo.456"]
        mock_resolve_doi.side_effect = [
            ResolverError("HTTP 406"),
            ResolverError("HTTP 406"),
        ]

        with pytest.raises(ResolverError, match="All 2 search result"):
            resolve_to_bibtex(SEARCH_QUERY_A, max_results=2)
