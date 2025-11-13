#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # PyYAML is optional; fall back to JSON-only metadata
    yaml = None

DEFAULT_GLOBAL_REPLACEMENTS = [
    {
        "pattern": r',\s*doi:\[(.*?)\]\((.*?)\)',
        "replacement": r' [[doi]](\2)',
    }
]

DEFAULT_AUTHOR_FLAG_SYMBOLS = {"first": "†", "corresponding": "*"}
DEFAULT_AUTHOR_FLAG_ORDER = ["first", "corresponding"]


def load_metadata(path: Path) -> dict:
    """Load metadata from JSON or YAML."""
    content = path.read_text(encoding="utf-8")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        if yaml is None:
            raise
        return yaml.safe_load(content) or {}


def normalize_doi(value: str) -> str:
    return value.strip().lower()


def extract_doi(text: str) -> str | None:
    match = re.search(r"(10\.\d{4,9}/[^\s\)]+)", text)
    return match.group(1) if match else None


def apply_regex_operations(text: str, operations: list[dict] | None) -> str:
    if not operations:
        return text
    for op in operations:
        pattern = op.get("pattern")
        replacement = op.get("replacement")
        if not pattern or replacement is None:
            continue
        text = re.sub(pattern, replacement, text)
    return text


def apply_author_replacements(text: str, replacements: list[dict] | None) -> str:
    if not replacements:
        return text
    for replacement in replacements:
        target = replacement.get("match")
        output = replacement.get("replacement")
        if not target or output is None:
            continue
        if replacement.get("regex"):
            text = re.sub(target, output, text)
        else:
            text = text.replace(target, output)
    return text


def find_metadata_entry(
    text: str,
    doi_index: dict[str, dict],
    entries: list[dict],
) -> dict | None:
    doi = extract_doi(text)
    if doi:
        normalized = normalize_doi(doi)
        entry = doi_index.get(normalized)
        if entry:
            return entry
    for entry in entries:
        match_text = entry.get("match_text")
        if match_text and match_text in text:
            return entry
        match_pattern = entry.get("match_pattern")
        if match_pattern and re.search(match_pattern, text):
            return entry
    return None


def highlight_author(text: str, author: str, template: str) -> str:
    if not author:
        return text
    return text.replace(author, template.format(name=author))


def merge_dict(base: dict, override: dict | None) -> dict:
    result = dict(base)
    if override:
        result.update(override)
    return result


def build_author_flag_settings(metadata: dict, entry: dict) -> tuple[dict[str, str], list[str]]:
    symbols = merge_dict(DEFAULT_AUTHOR_FLAG_SYMBOLS, metadata.get("author_flag_symbols"))
    symbols = merge_dict(symbols, entry.get("author_flag_symbols"))

    explicit_order = entry.get("author_flag_order") or metadata.get("author_flag_order")
    if explicit_order and isinstance(explicit_order, str):
        explicit_order = [explicit_order]
    order = list(dict.fromkeys(explicit_order or DEFAULT_AUTHOR_FLAG_ORDER))

    # Ensure flags defined in symbols appear in the order list.
    for flag in symbols:
        if flag not in order:
            order.append(flag)

    return symbols, order


def collect_author_statuses(entry: dict, flag_keys: list[str]) -> dict[str, list[str]]:
    statuses: dict[str, list[str]] = {}
    for flag in flag_keys:
        for name in entry.get(f"{flag}_authors", []):
            statuses.setdefault(name, []).append(flag)
    return statuses


def escape_markdown_symbol(text: str) -> str:
    escape_chars = r'\`*_{}[]()#+-.!'
    return "".join(f"\\{c}" if c in escape_chars else c for c in text)


def apply_author_flags(
    text: str,
    statuses: dict[str, list[str]],
    symbols: dict[str, str],
    flag_order: list[str],
) -> str:
    for name, flags in statuses.items():
        tokens: list[str] = []
        for flag in flag_order:
            if flag in flags:
                token = symbols.get(flag)
                if token:
                    tokens.append(escape_markdown_symbol(token))
        if not tokens:
            continue
        suffix = f"^{''.join(tokens)}^"
        if name + suffix in text:
            continue
        text = text.replace(name, f"{name}{suffix}")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply metadata-driven fixes to the reference output.",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        type=Path,
        help="JSON or YAML file describing per-reference replacements.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("outputs/ref_output.md"),
        help="Path to the reference markdown to reformat.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("outputs/ref_output_edit.md"),
        help="Path for the reformatted reference markdown.",
    )
    parser.add_argument(
        "author_name",
        nargs="?",
        help="Legacy positional author name to highlight (kept for compatibility).",
    )
    parser.add_argument(
        "-a",
        "--author",
        help="Highlight every occurrence of this author using the provided template.",
    )
    parser.add_argument(
        "--author-template",
        default="**{name}**",
        help="Template used for --author (default bold).",
    )
    args = parser.parse_args()

    if args.author_name and not args.author:
        args.author = args.author_name

    metadata = load_metadata(args.metadata) if args.metadata else {}
    reference_entries = metadata.get("references", []) if metadata else []
    doi_index: dict[str, dict] = {}
    for entry in reference_entries:
        doi = entry.get("doi")
        if doi:
            doi_index[normalize_doi(doi)] = entry

    global_replacements = list(DEFAULT_GLOBAL_REPLACEMENTS)
    global_replacements.extend(metadata.get("global_text_replacements") or [])

    raw_content = args.input.read_text(encoding="utf-8")
    single_line = re.sub(r"(?<!\n)\n(?!\n)", " ", raw_content)
    refs = re.findall(
        r'<span class="csl-left-margin">(.*?)<\/span>.*?<span class="csl-right-inline">(.*?)<\/span>',
        single_line,
        re.MULTILINE | re.DOTALL,
    )

    formatted_refs: list[str] = []
    for left, right in refs:
        updated_text = apply_regex_operations(right, global_replacements)
        entry = find_metadata_entry(updated_text, doi_index, reference_entries)
        if entry:
            updated_text = apply_regex_operations(
                updated_text, entry.get("text_replacements")
            )
            updated_text = apply_author_replacements(
                updated_text, entry.get("author_replacements")
            )
            symbols, flag_order = build_author_flag_settings(metadata, entry)
            statuses = collect_author_statuses(entry, flag_order)
            updated_text = apply_author_flags(
                updated_text, statuses, symbols, flag_order
            )
        if args.author:
            updated_text = highlight_author(
                updated_text, args.author, args.author_template
            )
        formatted_refs.append(f"{left} {updated_text}")

    args.output.write_text("\n\n".join(formatted_refs).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
