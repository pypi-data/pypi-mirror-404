"""Command-line interface for fetchbib.

Entry point: ``fbib``
"""

import argparse
import sys

from fetchbib import config
from fetchbib.resolver import (
    ResolverError,
    is_doi,
    normalize_doi_input,
    resolve_to_bibtex,
)


def _normalize_for_dedup(query: str) -> str:
    """Normalize a query for deduplication purposes.

    Strips DOI URL prefixes and lowercases DOIs so that different
    representations of the same DOI are treated as duplicates.
    """
    normalized = normalize_doi_input(query)
    if is_doi(normalized):
        return normalized.lower()
    return query  # Keep free-text queries as-is for dedup


def main() -> None:
    """Parse arguments and resolve each input to formatted BibTeX."""
    parser = argparse.ArgumentParser(
        prog="fbib",
        description="Resolve DOIs or search queries into formatted BibTeX.",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help=(
            "DOIs (e.g., 10.1234/example), DOI URLs (e.g., https://doi.org/10.1234/example), "
            'or quoted free-text queries (e.g., "Author Title 2024"). '
            "Comma-separated values are split."
        ),
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Path to a text file with one input per line",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write results to this file instead of stdout",
    )
    parser.add_argument(
        "-a",
        "--append",
        action="store_true",
        help="Append to the output file instead of overwriting (requires --output)",
    )
    parser.add_argument(
        "-n",
        "--max-results",
        type=int,
        default=1,
        help="Max results per free-text search (1-100, default: 1)",
    )
    parser.add_argument(
        "--config-api-key",
        metavar="KEY",
        help="Set your OpenAlex API key (get one free at openalex.org) and exit",
    )
    parser.add_argument(
        "--config-protect-titles",
        action="store_true",
        help="Toggle double-bracing of titles and exit",
    )
    parser.add_argument(
        "--config-exclude-issn",
        action="store_true",
        help="Toggle exclusion of ISSN from BibTeX entries and exit",
    )
    parser.add_argument(
        "--config-exclude-doi",
        action="store_true",
        help="Toggle exclusion of DOI from BibTeX entries and exit",
    )

    args = parser.parse_args()

    # --append requires --output
    if args.append and not args.output:
        parser.error("--append requires --output")

    # Validate --max-results range
    if args.max_results < 1 or args.max_results > 100:
        parser.error("--max-results must be between 1 and 100")

    # --config-api-key: save and exit immediately
    if args.config_api_key:
        config.set_openalex_api_key(args.config_api_key)
        print("OpenAlex API key saved.")
        sys.exit(0)

    # --config-protect-titles: toggle and exit immediately
    if args.config_protect_titles:
        new_value = not config.get_protect_titles()
        config.set_protect_titles(new_value)
        state = "enabled (double-braced titles)" if new_value else "disabled"
        print(f"Title protection {state}.")
        sys.exit(0)

    # --config-exclude-issn: toggle and exit immediately
    if args.config_exclude_issn:
        new_value = not config.get_exclude_issn()
        config.set_exclude_issn(new_value)
        state = "enabled (ISSN excluded)" if new_value else "disabled"
        print(f"ISSN exclusion {state}.")
        sys.exit(0)

    # --config-exclude-doi: toggle and exit immediately
    if args.config_exclude_doi:
        new_value = not config.get_exclude_doi()
        config.set_exclude_doi(new_value)
        state = "enabled (DOI excluded)" if new_value else "disabled"
        print(f"DOI exclusion {state}.")
        sys.exit(0)

    # Collect inputs
    queries = _collect_inputs(args)
    if not queries:
        print(
            "Error: no inputs provided. Pass DOIs/queries as arguments or use --file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if -n was explicitly set but there are no free-text queries
    max_results_explicitly_set = "-n" in sys.argv or "--max-results" in sys.argv
    has_free_text = any(not is_doi(normalize_doi_input(q)) for q in queries)
    if max_results_explicitly_set and not has_free_text:
        parser.error("--max-results requires at least one free-text query")

    # Resolve each input
    results: list[str] = []
    had_error = False

    for query in queries:
        try:
            bibtex_entries = _resolve_single(query, max_results=args.max_results)
            results.extend(bibtex_entries)
        except ResolverError as exc:
            print(f"Error resolving '{query}': {exc}", file=sys.stderr)
            had_error = True

    output_text = "\n\n".join(results)
    if results:
        output_text += "\n"

    # Write output
    if args.output:
        mode = "a" if args.append else "w"
        with open(args.output, mode) as f:
            f.write(output_text)
    else:
        print(output_text, end="")

    if had_error:
        sys.exit(1)


def _collect_inputs(args: argparse.Namespace) -> list[str]:
    """Gather inputs from positional args and --file, deduplicate."""
    raw: list[str] = []

    # Positional args (may be comma-separated DOIs, but not free-text)
    for arg in args.inputs or []:
        raw.extend(_smart_split(arg))

    # File input (each line may also be comma-separated DOIs)
    if args.file:
        try:
            with open(args.file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        raw.extend(_smart_split(line))
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)

    # Deduplicate preserving order, normalizing for comparison
    seen: set[str] = set()
    unique: list[str] = []
    for item in raw:
        key = _normalize_for_dedup(item)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _smart_split(value: str) -> list[str]:
    """Split on commas only if all parts look like DOIs.

    This prevents search queries containing commas (e.g., author names)
    from being incorrectly split into multiple queries.
    """
    if "," not in value:
        return [value.strip()] if value.strip() else []

    parts = [part.strip() for part in value.split(",") if part.strip()]

    # Only split if ALL parts look like DOIs (bare or URL form)
    if all(is_doi(normalize_doi_input(p)) for p in parts):
        return parts

    # Otherwise, treat the whole thing as a single query
    return [value.strip()] if value.strip() else []


def _resolve_single(query: str, *, max_results: int) -> list[str]:
    """Resolve a single query to formatted BibTeX entries.

    Returns a list with one entry for DOIs, or up to max_results for free-text.
    For free-text searches, individual DOI failures are warned but don't stop
    processing of other results.
    """
    return resolve_to_bibtex(
        query,
        max_results=max_results,
        protect_titles=config.get_protect_titles(),
        exclude_issn=config.get_exclude_issn(),
        exclude_doi=config.get_exclude_doi(),
    )
