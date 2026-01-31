"""Tests for the CLI (Phase 3).

All resolver calls are mocked — no network access needed.
"""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import DOI_A, DOI_B, DOI_URL_A, RAW_BIBTEX_A, RAW_BIBTEX_B, SEARCH_QUERY_A
from fetchbib.resolver import ResolverError


def run_cli(args: list[str]) -> tuple[int, str, str]:
    """Run the CLI main() with the given args, returning (exit_code, stdout, stderr)."""
    from fetchbib.cli import main

    old_argv = sys.argv
    sys.argv = ["fbib"] + args

    stdout_capture = StringIO()
    stderr_capture = StringIO()

    exit_code = 0
    try:
        with patch("sys.stdout", stdout_capture), patch("sys.stderr", stderr_capture):
            main()
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    finally:
        sys.argv = old_argv

    return exit_code, stdout_capture.getvalue(), stderr_capture.getvalue()


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------


class TestInputParsing:
    """Tests for how the CLI collects and processes inputs."""

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_single_positional_doi(self, mock_resolve):
        code, stdout, _ = run_cli([DOI_A])

        mock_resolve.assert_called_once_with(DOI_A)
        assert "@article{Key1," in stdout
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_multiple_positional_arguments(self, mock_resolve):
        code, stdout, _ = run_cli([DOI_A, DOI_B])

        assert mock_resolve.call_count == 2
        assert "Key1" in stdout
        assert "Key2" in stdout
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_comma_separated_dois_are_split(self, mock_resolve):
        code, stdout, _ = run_cli([f"{DOI_A}, {DOI_B}"])

        assert mock_resolve.call_count == 2
        calls = [c.args[0] for c in mock_resolve.call_args_list]
        assert DOI_A in calls
        assert DOI_B in calls
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    @patch("fetchbib.resolver.search_openalex", return_value=[DOI_A])
    def test_comma_in_search_query_not_split(self, mock_search, mock_resolve):
        """Commas in free-text queries are preserved, not treated as separators."""
        code, stdout, _ = run_cli(["Smith, John machine learning"])

        # Should be treated as a single search query, not split
        mock_search.assert_called_once()
        query_arg = mock_search.call_args[0][0]
        assert "Smith, John" in query_arg
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_file_input_reads_lines(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{DOI_A}\n\n{DOI_B}\n")
            f.flush()
            code, stdout, _ = run_cli(["--file", f.name])

        assert mock_resolve.call_count == 2
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_file_input_splits_comma_separated_dois(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{DOI_A}, {DOI_B}\n")
            f.flush()
            code, stdout, _ = run_cli(["--file", f.name])

        assert mock_resolve.call_count == 2
        calls = [c.args[0] for c in mock_resolve.call_args_list]
        assert DOI_A in calls
        assert DOI_B in calls
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_doi_url_is_normalized(self, mock_resolve):
        code, stdout, _ = run_cli([DOI_URL_A])

        mock_resolve.assert_called_once_with(DOI_A)
        assert "@article{Key1," in stdout
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_duplicate_inputs_are_deduplicated(self, mock_resolve):
        code, _, _ = run_cli([DOI_A, DOI_A])

        mock_resolve.assert_called_once()
        assert code == 0

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_doi_and_doi_url_are_deduplicated(self, mock_resolve):
        """DOI and its URL form are treated as duplicates."""
        code, _, _ = run_cli([DOI_A, DOI_URL_A])

        mock_resolve.assert_called_once()
        assert code == 0

    @patch("fetchbib.resolver.resolve_arxiv", return_value="@misc{key,author={A}}")
    def test_arxiv_dois_case_insensitive_dedup(self, mock_arxiv):
        """arXiv DOIs with different casing are deduplicated."""
        code, _, _ = run_cli(["10.48550/arXiv.2410.21554", "10.48550/arxiv.2410.21554"])

        mock_arxiv.assert_called_once()
        assert code == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error conditions and exit codes."""

    def test_nonexistent_file_exits_1(self):
        code, _, stderr = run_cli(["--file", "nonexistent_file.txt"])

        assert code == 1
        assert "nonexistent_file.txt" in stderr

    @patch("fetchbib.resolver.resolve_doi")
    def test_resolution_error_does_not_stop_others(self, mock_resolve):
        mock_resolve.side_effect = [
            ResolverError("fail"),
            RAW_BIBTEX_B,
        ]

        code, stdout, stderr = run_cli(["10.1234/bad", "10.1234/good"])

        assert "Key2" in stdout
        assert "fail" in stderr
        assert code == 1

    def test_no_inputs_exits_1(self):
        code, _, stderr = run_cli([])

        assert code == 1
        assert stderr  # should contain some usage hint


# ---------------------------------------------------------------------------
# Max results
# ---------------------------------------------------------------------------


class TestMaxResults:
    """Tests for the --max-results flag."""

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    @patch("fetchbib.resolver.search_openalex", return_value=[DOI_A])
    def test_default_returns_one_result(self, mock_search, mock_resolve):
        code, stdout, _ = run_cli([SEARCH_QUERY_A])

        mock_search.assert_called_once_with(SEARCH_QUERY_A, 1)
        assert mock_resolve.call_count == 1
        assert code == 0

    @pytest.mark.parametrize("n", ["0", "101", "-1"])
    def test_n_out_of_range_exits_with_code_2(self, n):
        code, _, stderr = run_cli(["-n", n, SEARCH_QUERY_A])

        assert code == 2
        assert "between 1 and 100" in stderr

    def test_n_with_only_dois_exits_with_code_2(self):
        code, _, stderr = run_cli(["-n", "5", DOI_A])

        assert code == 2
        assert "free-text" in stderr

    @patch(
        "fetchbib.resolver.search_openalex",
        return_value=[DOI_A, "10.9999/broken", DOI_B],
    )
    @patch("fetchbib.resolver.resolve_doi")
    def test_partial_failure_returns_successful_results(
        self, mock_resolve, mock_search
    ):
        """When one DOI fails, the others should still be returned."""
        mock_resolve.side_effect = [
            RAW_BIBTEX_A,
            ResolverError("HTTP 500"),
            RAW_BIBTEX_B,
        ]

        code, stdout, stderr = run_cli(["-n", "3", SEARCH_QUERY_A])

        assert code == 0
        assert "Key1" in stdout
        assert "Key2" in stdout
        assert "Warning" in stderr
        assert "10.9999/broken" in stderr
        assert "https://doi.org/10.9999/broken" in stderr


# ---------------------------------------------------------------------------
# Output file
# ---------------------------------------------------------------------------


class TestOutputFile:
    """Tests for --output and --append flags."""

    def test_append_without_output_exits_2(self):
        code, _, stderr = run_cli(["--append", "10.1234/test"])

        assert code == 2
        assert "--append requires --output" in stderr

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_output_writes_to_file(self, mock_resolve):
        with tempfile.NamedTemporaryFile(suffix=".bib", delete=False) as f:
            path = f.name

        code, stdout, _ = run_cli(["--output", path, "10.1234/test"])

        assert code == 0
        assert stdout == ""  # nothing to stdout
        content = Path(path).read_text()
        assert "Key1" in content

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_output_overwrites_by_default(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write("OLD CONTENT\n")
            path = f.name

        run_cli(["--output", path, "10.1234/test"])

        content = Path(path).read_text()
        assert "OLD CONTENT" not in content
        assert "Key1" in content

    @patch("fetchbib.resolver.resolve_doi", return_value=RAW_BIBTEX_B)
    def test_append_flag_preserves_existing(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write("EXISTING ENTRY\n\n")
            path = f.name

        code, stdout, _ = run_cli(["--append", "--output", path, "10.1234/test"])

        assert code == 0
        assert stdout == ""
        content = Path(path).read_text()
        assert "EXISTING ENTRY" in content
        assert "Key2" in content


# ---------------------------------------------------------------------------
# Config API key
# ---------------------------------------------------------------------------


class TestConfigApiKey:
    """Tests for --config-api-key."""

    def test_config_api_key_saves_and_exits(self, tmp_path):
        config_file = tmp_path / "config.json"
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, stdout, _ = run_cli(["--config-api-key", "my_openalex_key_123"])

        assert code == 0
        assert "OpenAlex API key saved" in stdout
        saved = json.loads(config_file.read_text())
        assert saved["openalex_api_key"] == "my_openalex_key_123"


# ---------------------------------------------------------------------------
# Config protect-titles
# ---------------------------------------------------------------------------


class TestConfigProtectTitles:
    """Tests for --config-protect-titles toggle."""

    def test_config_protect_titles_toggles_false_to_true(self, tmp_path):
        config_file = tmp_path / "config.json"
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, stdout, _ = run_cli(["--config-protect-titles"])

        assert code == 0
        assert "enabled" in stdout.lower()
        saved = json.loads(config_file.read_text())
        assert saved["protect_titles"] is True

    def test_config_protect_titles_toggles_true_to_false(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"protect_titles": True}))
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, stdout, _ = run_cli(["--config-protect-titles"])

        assert code == 0
        assert "disabled" in stdout.lower()
        saved = json.loads(config_file.read_text())
        assert saved["protect_titles"] is False


# ---------------------------------------------------------------------------
# Config exclude-issn
# ---------------------------------------------------------------------------


class TestConfigExcludeIssn:
    """Tests for --config-exclude-issn toggle."""

    def test_config_exclude_issn_toggles_false_to_true(self, tmp_path):
        config_file = tmp_path / "config.json"
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, stdout, _ = run_cli(["--config-exclude-issn"])

        assert code == 0
        assert "enabled" in stdout.lower()
        saved = json.loads(config_file.read_text())
        assert saved["exclude_issn"] is True

    def test_config_exclude_issn_toggles_true_to_false(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"exclude_issn": True}))
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, stdout, _ = run_cli(["--config-exclude-issn"])

        assert code == 0
        assert "disabled" in stdout.lower()
        saved = json.loads(config_file.read_text())
        assert saved["exclude_issn"] is False


# ---------------------------------------------------------------------------
# Config exclude-doi
# ---------------------------------------------------------------------------


class TestConfigExcludeDoi:
    """Tests for --config-exclude-doi toggle."""

    def test_config_exclude_doi_toggles_false_to_true(self, tmp_path):
        config_file = tmp_path / "config.json"
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, stdout, _ = run_cli(["--config-exclude-doi"])

        assert code == 0
        assert "enabled" in stdout.lower()
        saved = json.loads(config_file.read_text())
        assert saved["exclude_doi"] is True

    def test_config_exclude_doi_toggles_true_to_false(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"exclude_doi": True}))
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, stdout, _ = run_cli(["--config-exclude-doi"])

        assert code == 0
        assert "disabled" in stdout.lower()
        saved = json.loads(config_file.read_text())
        assert saved["exclude_doi"] is False
