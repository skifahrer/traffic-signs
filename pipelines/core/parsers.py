"""Readers for the ways Wikipedia lists traffic signs.

Each factory returns a parser: a function from page wikitext to
`(entries, problems)`. A country picks one or more in its `Source`, passing the
regular expression its sign codes follow and the local name of the File:
namespace.

    gallery(...)    <gallery> lines:  File:<image>|<code> <name>
    wikitable(...)  table rows:       | [[File:<image>|120px]] || <code> <name> || ...

A page laid out some other way needs a new parser: add a factory here when
other countries could use it, or write the function in the country's own
package (countries/<code>/parser.py) when it is specific to that page.
"""

from __future__ import annotations

import re
from typing import Sequence, Union

from .model import Entry, Parser, Problem
from .wikimedia import strip_markup

DEFAULT_NAMESPACES = ("File", "Image")


Patterns = Union[str, Sequence[str], None]


def gallery(code_pattern: str, namespaces: tuple[str, ...] = (), ignore: Patterns = None, strip: str | None = None) -> Parser:
    """Entries from `<gallery>` blocks whose captions start with the sign code.

    `ignore`: regular expression(s) for captions that are not signs (symbols,
    road markings, outdated numbering, ...); they are skipped instead of
    reported as problems. `strip`: a regular expression removed from names.
    """
    line_re = re.compile(rf"^\s*(?:{_alternatives(namespaces)})\s*:\s*([^|]+?)\s*\|(.*)$", re.IGNORECASE)
    patterns = _Patterns(code_pattern, ignore, strip)

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        captions = _Captions(patterns)
        in_gallery = False
        for line in wikitext.splitlines():
            if re.match(r"\s*<gallery\b", line, re.IGNORECASE):
                in_gallery = True
            elif re.match(r"\s*</gallery>", line, re.IGNORECASE):
                in_gallery = False
            elif in_gallery and (match := line_re.match(line)):
                captions.add(match.group(1), match.group(2))
        return captions.entries, captions.problems

    parse.label = f"gallery({code_pattern})"
    return parse


def wikitable(code_pattern: str, namespaces: tuple[str, ...] = (), ignore: Patterns = None, strip: str | None = None) -> Parser:
    """Entries from table rows: an image cell followed by a cell starting with the sign code.

    `ignore` and `strip` work as for `gallery()`.
    """
    image_re = re.compile(rf"\[\[\s*(?:{_alternatives(namespaces)})\s*:\s*([^|\]]+)", re.IGNORECASE)
    patterns = _Patterns(code_pattern, ignore, strip)

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        captions = _Captions(patterns)
        for row in re.split(r"^\s*\|-.*$", wikitext, flags=re.MULTILINE):
            cells = _cells(row)
            for index, cell in enumerate(cells[:-1]):
                image = image_re.search(cell)
                if image:
                    captions.add(image.group(1), cells[index + 1])
                    break
        return captions.entries, captions.problems

    parse.label = f"wikitable({code_pattern})"
    return parse


def _alternatives(namespaces: tuple[str, ...]) -> str:
    return "|".join(re.escape(ns) for ns in (*namespaces, *DEFAULT_NAMESPACES))


class _Patterns:
    def __init__(self, code_pattern: str, ignore: Patterns, strip: str | None):
        self.caption = re.compile(rf"^({code_pattern}):?\s+(.+)$")
        ignore = [ignore] if isinstance(ignore, str) else list(ignore or [])
        self.ignore = re.compile("|".join(f"(?:{p})" for p in ignore)) if ignore else None
        self.strip = re.compile(strip) if strip else None


class _Captions:
    """Collects (image, caption) pairs as entries (`<code> <name>`) or problems."""

    QUOTES = " „“”\"'«»"

    def __init__(self, patterns: _Patterns):
        self.patterns = patterns
        self.entries: list[Entry] = []
        self.problems: list[Problem] = []

    def add(self, file: str, caption: str) -> None:
        file, text = file.strip().replace("_", " "), strip_markup(caption)
        if self.patterns.ignore and self.patterns.ignore.search(text):
            return
        match = self.patterns.caption.match(text)
        if match:
            name = self.patterns.strip.sub("", match.group(2)) if self.patterns.strip else match.group(2)
            self.entries.append(Entry(file=file, code=match.group(1), name=name.strip(self.QUOTES)))
        else:
            self.problems.append(Problem(file, f"caption without a sign code: `{file}` → `{text}`"))


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
