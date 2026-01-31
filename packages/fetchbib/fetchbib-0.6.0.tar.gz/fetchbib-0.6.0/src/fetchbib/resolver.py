"""DOI resolution and OpenAlex search.

Provides functions to check if a string is a DOI, resolve a DOI to BibTeX,
search OpenAlex for a DOI, and an orchestrator that combines them.
"""

import re
import sys

import requests

from fetchbib import config

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
DOI_URL_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
)

DOI_BASE_URL = "https://doi.org/"
OPENALEX_API_URL = "https://api.openalex.org/works"

ARXIV_DOI_PREFIX = "10.48550/arxiv."
ARXIV_BIBTEX_URL = "https://arxiv.org/bibtex/"

USER_AGENT = "fetchbib/1.0"


class ResolverError(Exception):
    """Raised when DOI resolution or OpenAlex search fails."""


def normalize_doi_input(value: str) -> str:
    """Strip common DOI URL prefixes, returning a bare DOI if possible.

    For example, ``https://doi.org/10.2196/jmir.1933`` becomes
    ``10.2196/jmir.1933``. Non-URL strings are returned unchanged.
    """
    for prefix in DOI_URL_PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def is_doi(value: str) -> bool:
    """Return True if *value* looks like a bare DOI (e.g. 10.xxxx/yyyy)."""
    return bool(DOI_PATTERN.match(value))


def is_arxiv_doi(doi: str) -> bool:
    """Return True if doi is an arXiv DOI (10.48550/arXiv.*)."""
    return doi.lower().startswith(ARXIV_DOI_PREFIX)


def extract_arxiv_id(doi: str) -> str:
    """Extract arXiv ID from an arXiv DOI (case-insensitive prefix)."""
    return doi[len(ARXIV_DOI_PREFIX) :]


def resolve_doi(doi: str) -> str:
    """Fetch BibTeX for a DOI from doi.org.

    Raises ResolverError on non-200 responses.
    """
    headers = {
        "Accept": "text/bibliography; style=bibtex",
        "User-Agent": USER_AGENT,
    }
    resp = requests.get(f"{DOI_BASE_URL}{doi}", headers=headers)
    if resp.status_code != 200:
        raise ResolverError(
            f"DOI resolution failed for '{doi}': HTTP {resp.status_code}"
        )
    # doi.org returns UTF-8 content but without charset in Content-Type,
    # causing requests to default to ISO-8859-1. Decode as UTF-8 explicitly.
    return resp.content.decode("utf-8")


def resolve_arxiv(arxiv_id: str) -> str:
    """Fetch BibTeX for an arXiv paper.

    Raises ResolverError on non-200 responses.
    """
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(f"{ARXIV_BIBTEX_URL}{arxiv_id}", headers=headers)
    if resp.status_code != 200:
        raise ResolverError(
            f"arXiv resolution failed for '{arxiv_id}': HTTP {resp.status_code}"
        )
    return resp.content.decode("utf-8")


def _warn_no_api_key_once(remaining: str) -> None:
    """Print a warning about missing API key, but only once per session."""
    if getattr(_warn_no_api_key_once, "_shown", False):
        return
    _warn_no_api_key_once._shown = True
    print(
        f"Warning: No OpenAlex API key configured. "
        f"Daily limit credits remaining: {remaining}. "
        f"Set one with: fbib --config-api-key YOUR_KEY",
        file=sys.stderr,
    )


def search_openalex(query: str, max_results: int = 1) -> list[str]:
    """Search OpenAlex and return up to max_results DOIs.

    Raises ResolverError on non-200 responses or empty results.
    Shows a warning to stderr if no API key is configured.
    """
    api_key = config.get_openalex_api_key()
    headers = {"User-Agent": USER_AGENT}
    params: dict[str, str | int] = {"search": query, "per_page": max_results}
    if api_key:
        params["api_key"] = api_key

    resp = requests.get(OPENALEX_API_URL, params=params, headers=headers)
    if resp.status_code != 200:
        raise ResolverError(f"OpenAlex search failed: HTTP {resp.status_code}")

    if not api_key:
        remaining = resp.headers.get("X-RateLimit-Remaining", "unknown")
        _warn_no_api_key_once(remaining)

    results = resp.json()["results"]
    if not results:
        raise ResolverError(f"No results found for query: '{query}'")

    dois = []
    for item in results:
        doi_url = item.get("doi")
        if doi_url:
            doi = doi_url.removeprefix("https://doi.org/")
            dois.append(doi)
        if len(dois) >= max_results:
            break

    if not dois:
        raise ResolverError(f"No results with DOIs found for query: '{query}'")
    return dois


def resolve_to_bibtex(
    query: str,
    *,
    max_results: int = 1,
    protect_titles: bool = False,
    exclude_issn: bool = False,
    exclude_doi: bool = False,
) -> list[str]:
    """Resolve a query to formatted BibTeX entries.

    Accepts DOIs (bare or URL form), arXiv DOIs, or free-text search queries.
    Returns a list of formatted BibTeX strings.

    For DOIs, returns a single-item list.
    For free-text searches, returns up to max_results entries.

    Individual DOI failures during free-text searches are warned but don't
    stop processing of other results.
    """
    from fetchbib.formatter import format_bibtex

    query = normalize_doi_input(query)

    def _format(raw: str) -> str:
        return format_bibtex(
            raw,
            protect_titles=protect_titles,
            exclude_issn=exclude_issn,
            exclude_doi=exclude_doi,
        )

    if is_doi(query):
        if is_arxiv_doi(query):
            raw = resolve_arxiv(extract_arxiv_id(query))
        else:
            raw = resolve_doi(query)
        try:
            return [_format(raw)]
        except ValueError as exc:
            raise ResolverError(f"Invalid BibTeX response for '{query}': {exc}")

    dois = search_openalex(query, max_results)
    results = []
    failed_count = 0
    for doi in dois:
        try:
            if is_arxiv_doi(doi):
                raw = resolve_arxiv(extract_arxiv_id(doi))
            else:
                raw = resolve_doi(doi)
            results.append(_format(raw))
        except (ResolverError, ValueError) as exc:
            failed_count += 1
            print(
                f"Warning: Could not fetch BibTeX for {doi} ({exc}). "
                f"Try: https://doi.org/{doi}",
                file=sys.stderr,
            )

    # If all DOIs failed, raise an error
    if not results and failed_count > 0:
        raise ResolverError(
            f"All {failed_count} search result(s) failed to resolve for: '{query}'"
        )

    return results
