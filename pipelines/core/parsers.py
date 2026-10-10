"""Readers for the ways Wikipedia lists traffic signs.

Each factory returns a parser: a function from page wikitext to
`(entries, problems)`. A country picks one in its `Source`, passing the regular
expression its sign codes follow and the local name of the File: namespace.

    gallery(...)    <gallery> lines:  File:<image>|<code> <name>
    wikitable(...)  table rows:       | [[File:<image>|120px]] || <code> <name> || ...
"""

from __future__ import annotations

import re

from .model import Entry, Parser
from .wikimedia import strip_markup

DEFAULT_NAMESPACES = ("File", "Image")


def gallery(code_pattern: str, namespaces: tuple[str, ...] = ()) -> Parser:
    """Entries from `<gallery>` blocks whose captions start with the sign code."""
    line_re = re.compile(rf"^\s*(?:{_alternatives(namespaces)})\s*:\s*([^|]+?)\s*\|(.*)$", re.IGNORECASE)
    caption_re = _caption_re(code_pattern)

    def parse(wikitext: str) -> tuple[list[Entry], list[str]]:
        entries, problems = [], []
        in_gallery = False
        for line in wikitext.splitlines():
            if re.match(r"\s*<gallery\b", line, re.IGNORECASE):
                in_gallery = True
            elif re.match(r"\s*</gallery>", line, re.IGNORECASE):
                in_gallery = False
            elif in_gallery and (match := line_re.match(line)):
                _add(entries, problems, match.group(1), match.group(2), caption_re)
        return entries, problems

    return parse


def wikitable(code_pattern: str, namespaces: tuple[str, ...] = ()) -> Parser:
    """Entries from table rows: an image cell followed by a cell starting with the sign code."""
    image_re = re.compile(rf"\[\[\s*(?:{_alternatives(namespaces)})\s*:\s*([^|\]]+)", re.IGNORECASE)
    caption_re = _caption_re(code_pattern)

    def parse(wikitext: str) -> tuple[list[Entry], list[str]]:
        entries, problems = [], []
        for row in re.split(r"^\s*\|-.*$", wikitext, flags=re.MULTILINE):
            cells = _cells(row)
            for index, cell in enumerate(cells[:-1]):
                image = image_re.search(cell)
                if image:
                    _add(entries, problems, image.group(1), cells[index + 1], caption_re)
                    break
        return entries, problems

    return parse


def _alternatives(namespaces: tuple[str, ...]) -> str:
    return "|".join(re.escape(ns) for ns in (*namespaces, *DEFAULT_NAMESPACES))


def _caption_re(code_pattern: str) -> re.Pattern:
    return re.compile(rf"^({code_pattern})\s+(.+)$")


def _add(entries: list[Entry], problems: list[str], file: str, caption: str, caption_re: re.Pattern) -> None:
    file, text = file.strip().replace("_", " "), strip_markup(caption)
    match = caption_re.match(text)
    if match:
        entries.append(Entry(file=file, code=match.group(1), name=match.group(2).strip()))
    else:
        problems.append(f"caption without a sign code: `{file}` → `{text}`")


def _cells(row: str) -> list[str]:
    """The data cells of one wikitable row, without their style attributes."""
    cells = []
    for line in row.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith(("|}", "|+", "|-")):
            continue
        for cell in line[1:].split("||"):
            # `align="center"|content`: drop the attributes, but not a link's `|`.
            attributes, bar, content = cell.partition("|")
            if bar and "[[" not in attributes and "=" in attributes:
                cell = content
            cells.append(cell.strip())
    return cells
