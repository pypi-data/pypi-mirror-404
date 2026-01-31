"""BibTeX string formatter.

Transforms raw (often single-line) BibTeX into a clean, readable format
with alphabetized fields, 2-space indentation, and proper line breaks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class BibTeXEntry:
    """Structured representation of a BibTeX entry.

    Provides methods for manipulating fields and converting to formatted output.
    """

    entry_type: str
    citation_key: str
    fields: list[tuple[str, str]] = field(default_factory=list)

    def remove_field(self, name: str) -> None:
        """Remove all fields matching the given name (case-insensitive)."""
        self.fields = [(k, v) for k, v in self.fields if k.lower() != name.lower()]

    def protect_title(self) -> None:
        """Transform the title field to use double braces (preserving case)."""
        self.fields = [
            (k, _protect_title(v) if k.lower() == "title" else v)
            for k, v in self.fields
        ]

    def sort_fields(self) -> None:
        """Sort fields alphabetically by key (case-insensitive)."""
        self.fields.sort(key=lambda kv: kv[0].lower())

    def to_formatted_string(self) -> str:
        """Convert to a formatted BibTeX string with proper indentation."""
        header = f"@{self.entry_type}{{{self.citation_key},"
        field_lines = [f"  {key} = {value}" for key, value in self.fields]
        return header + "\n" + ",\n".join(field_lines) + "\n}"

    @classmethod
    def from_raw_bibtex(cls, raw: str) -> BibTeXEntry:
        """Parse a raw BibTeX string into a BibTeXEntry.

        Handles single-line and multi-line input, cleans citation keys
        with multiple underscores, and preserves field values including
        nested braces.
        """
        header, fields_block = _split_header(raw.strip())
        header = _clean_citation_key(header)
        fields = _parse_fields(fields_block)

        # Parse entry type and citation key from header
        # Header format: @type{key,
        match = re.match(r"@(\w+)\{([^,]+),", header)
        if not match:
            # Truncate for cleaner error messages (e.g., when HTML is returned)
            preview = header[:50] + "..." if len(header) > 50 else header
            raise ValueError(f"Invalid BibTeX (expected @type{{key,...}}): {preview}")

        entry_type = match.group(1)
        citation_key = match.group(2)

        return cls(entry_type=entry_type, citation_key=citation_key, fields=fields)


def format_bibtex(
    raw: str,
    *,
    protect_titles: bool = False,
    exclude_issn: bool = False,
    exclude_doi: bool = False,
) -> str:
    """Format a raw BibTeX entry into a clean, readable string.

    Rules:
        - Entry header (@type{key,) stays on the first line.
        - Each field is on its own line with 2-space indentation.
        - Fields are alphabetized.
        - Closing brace is on its own line.
        - Trailing commas are removed.

    If protect_titles is True, the title field is transformed to use
    double braces (preserving case) with inner braces removed.

    If exclude_issn is True, the ISSN field is removed from the output.

    If exclude_doi is True, the DOI field is removed from the output.

    Commas inside braced values (e.g. author names) are preserved — only
    top-level commas are treated as field separators.
    """
    entry = BibTeXEntry.from_raw_bibtex(raw)

    if protect_titles:
        entry.protect_title()

    if exclude_issn:
        entry.remove_field("issn")

    if exclude_doi:
        entry.remove_field("doi")

    entry.sort_fields()

    return entry.to_formatted_string()


def _clean_citation_key(header: str) -> str:
    """Collapse multiple underscores in the citation key to a single underscore.

    The header has the form '@type{key,' — this function fixes keys like
    'Mesk__2023' that result from non-ASCII character stripping.
    """
    return re.sub(r"_+", "_", header)


def _protect_title(value: str) -> str:
    """Transform a braced title value to use double braces.

    Removes inner braces and wraps the content in double braces.
    Example: {This is {THE} title} -> {{This is THE title}}
    """
    # Strip outer braces if present
    stripped = value.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        inner = stripped[1:-1]
    else:
        inner = stripped

    # Remove all inner braces
    content = inner.replace("{", "").replace("}", "")

    return "{{" + content + "}}"


def _split_header(entry: str) -> tuple[str, str]:
    """Split a BibTeX entry into header and fields block.

    The header is everything up to and including the first top-level comma
    after the citation key (e.g. '@article{Key2020,').
    The fields block is the rest, minus the final closing '}'.
    """
    # Find the first comma that is not inside braces — this ends the key.
    depth = 0
    for i, ch in enumerate(entry):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "," and depth == 1:
            header = entry[: i + 1]
            rest = entry[i + 1 :]
            # Strip the outermost closing brace from the rest
            rest = rest.strip()
            if rest.endswith("}"):
                rest = rest[:-1].strip()
            return header, rest
    # Fallback: no fields found
    return entry, ""


def _parse_fields(block: str) -> list[tuple[str, str]]:
    """Parse a block of BibTeX fields into (key, value) pairs.

    Splits on top-level commas only (not commas inside braces).
    """
    if not block.strip():
        return []

    fields = []
    for raw_field in _split_top_level(block, ","):
        raw_field = raw_field.strip()
        if not raw_field:
            continue
        # Split on the first '=' to get key and value
        eq_pos = raw_field.find("=")
        if eq_pos == -1:
            continue
        key = raw_field[:eq_pos].strip()
        value = raw_field[eq_pos + 1 :].strip()
        fields.append((key, value))
    return fields


def _split_top_level(text: str, delimiter: str) -> list[str]:
    """Split text on a delimiter, but only at brace depth 0."""
    parts = []
    depth = 0
    current: list[str] = []

    for ch in text:
        if ch == "{":
            depth += 1
            current.append(ch)
        elif ch == "}":
            depth -= 1
            current.append(ch)
        elif ch == delimiter and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)

    # Append whatever is left
    trailing = "".join(current).strip()
    if trailing:
        parts.append(trailing)

    return parts
