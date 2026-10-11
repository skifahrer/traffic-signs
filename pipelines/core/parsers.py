"""Readers for the ways Wikipedia lists traffic signs.

Each factory returns a parser: a function from page wikitext to
`(entries, problems)`. A country picks one or more in its `Source`, passing the
regular expression its sign codes follow and the local name of the File:
namespace.

    gallery(...)    <gallery> lines:  File:<image>|<code> <name>
    wikitable(...)  table rows:       | [[File:<image>|120px]] || <code> <name> || ...
    files(...)      any image whose file name holds the code: "UK traffic sign 501.svg"
    named_files(...) <gallery> lines whose file name holds the code, named by their caption:
                    File:MUTCD R1-1.svg|R1-1<br>Stop
    between(...)    another parser, run on part of the page only (from one heading to another)

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


def gallery(
    code_pattern: str,
    namespaces: tuple[str, ...] = (),
    ignore: Patterns = None,
    strip: str | None = None,
    code_prefix: str | None = None,
) -> Parser:
    """Entries from `<gallery>` blocks whose captions start with the sign code.

    `ignore`: regular expression(s) for captions that are not signs (symbols,
    road markings, outdated numbering, ...); they are skipped instead of
    reported as problems. `strip`: a regular expression removed from names.
    `code_prefix`: a regular expression for the words every caption puts
    before the code, which are not part of it: "Zeichen " in
    "Zeichen 101 Gefahrstelle" gives code "101".
    """
    line_re = re.compile(rf"^\s*(?:{_alternatives(namespaces)})?\s*:?\s*([^|:\[\]]+\.[A-Za-z]{{3,4}})\s*\|(.*)$", re.IGNORECASE)
    patterns = _Patterns(code_pattern, ignore, strip, code_prefix)

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        captions = _Captions(patterns)
        in_gallery = False
        for line in wikitext.splitlines():
            if re.match(r"\s*<gallery\b", line, re.IGNORECASE):
                in_gallery = True
            elif re.match(r"\s*</gallery>", line, re.IGNORECASE):
                in_gallery = False
            elif in_gallery and (match := line_re.match(line)):
                captions.add(match.group(1), _GALLERY_OPTIONS.sub("", match.group(2)))
        return captions.entries, captions.problems

    parse.label = f"gallery({code_pattern})"
    return parse


def wikitable(
    code_pattern: str,
    namespaces: tuple[str, ...] = (),
    ignore: Patterns = None,
    strip: str | None = None,
    code_prefix: str | None = None,
) -> Parser:
    """Entries from table rows: an image cell followed by a cell starting with the sign code.

    `ignore`, `strip` and `code_prefix` work as for `gallery()`.
    """
    image_re = re.compile(rf"\[\[\s*(?:{_alternatives(namespaces)})\s*:\s*([^|\]]+)", re.IGNORECASE)
    patterns = _Patterns(code_pattern, ignore, strip, code_prefix)

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


def files(file_pattern: str, ignore: Patterns = None) -> Parser:
    """Entries for every image on the page whose file name matches `file_pattern`.

    For pages whose captions are missing or inconsistent but whose files are
    named after the sign, e.g. `UK traffic sign 512 (right).svg`. The pattern
    must match the whole file name (underscores read as spaces) and capture
    the code in a group named `code`:

        files(r"UK traffic sign (?P<code>.+)\\.svg")

    Images anywhere count: galleries, [[File:...]] links, tables, templates.
    Entries have no name, so use it with `Source(local_names="translations")`.
    Files that do not match are not signs and are skipped. `ignore`: regular
    expression(s) for matching file names that are still not signs.
    """
    file_re = re.compile(file_pattern)
    if "code" not in file_re.groupindex:
        raise ValueError(f"files(): the pattern needs a (?P<code>...) group: {file_pattern}")
    ignore = [ignore] if isinstance(ignore, str) else list(ignore or [])
    ignore_re = re.compile("|".join(f"(?:{p})" for p in ignore)) if ignore else None
    # A file name: from after `File:`, `[[`, `|`, `=` or a line start up to its extension.
    candidate_re = re.compile(r"(?:^|(?<=[:|=\[\n]))\s*([^:|=\[\]{}<>\n]+?\.(?:svg|png|jpe?g|gif|webp|tiff?))\b", re.IGNORECASE)

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        entries, seen = [], set()
        for candidate in candidate_re.finditer(wikitext):
            file = " ".join(candidate.group(1).replace("_", " ").split())
            match = file_re.fullmatch(file)
            if not match or (ignore_re and ignore_re.search(file)):
                continue
            code = match.group("code").strip()
            if (file, code) not in seen:
                seen.add((file, code))
                entries.append(Entry(file=file, code=code, name=""))
        return entries, []

    parse.label = f"files({file_pattern})"
    return parse


# Options before a gallery caption: `File:x.svg|alt=Text|Caption`.
_GALLERY_OPTIONS = re.compile(r"^(?:\s*(?:alt|alternativtext|link|page|lang|class)\s*=[^|]*\|)+", re.IGNORECASE)


def named_files(
    file_pattern: str,
    namespaces: tuple[str, ...] = (),
    caption_code: str | None = None,
    ignore: Patterns = None,
    strip: str | None = None,
) -> Parser:
    """Entries from `<gallery>` lines whose image name holds the code, named by the caption.

    For pages where variants of a sign (a yellow and a white version, a state
    variant) share the code in their captions but not their file names. The
    pattern must match the whole file name and capture the code in a group
    named `code`; lines with other images are skipped. `caption_code`: a
    regular expression for the code (or anything else) the caption starts
    with, which is not part of the name. `ignore`: regular expression(s) for
    the file name or caption of lines that are not signs. `strip`: removed
    from names.

        named_files(r"MUTCD (?P<code>[A-Z]+\d.*)\.svg", caption_code=r"[A-Z]+\d\S*\s+")
    """
    file_re = re.compile(file_pattern)
    if "code" not in file_re.groupindex:
        raise ValueError(f"named_files(): the pattern needs a (?P<code>...) group: {file_pattern}")
    line_re = re.compile(rf"^\s*(?:{_alternatives(namespaces)})?\s*:?\s*([^|:\[\]]+\.[A-Za-z]{{3,4}})\s*\|(.*)$", re.IGNORECASE)
    prefix_re = re.compile(rf"^(?:{caption_code})") if caption_code else None
    ignore = [ignore] if isinstance(ignore, str) else list(ignore or [])
    ignore_re = re.compile("|".join(f"(?:{p})" for p in ignore)) if ignore else None
    strip_re = re.compile(strip) if strip else None

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        entries: list[Entry] = []
        in_gallery = False
        for line in wikitext.splitlines():
            if re.match(r"\s*<gallery\b", line, re.IGNORECASE):
                in_gallery = True
            elif re.match(r"\s*</gallery>", line, re.IGNORECASE):
                in_gallery = False
            elif in_gallery and (match := line_re.match(line)):
                file = " ".join(match.group(1).replace("_", " ").split())
                found = file_re.fullmatch(file)
                if not found:
                    continue
                name = strip_markup(_GALLERY_OPTIONS.sub("", match.group(2)))
                if ignore_re and (ignore_re.search(file) or ignore_re.search(name)):
                    continue
                if prefix_re:
                    name = prefix_re.sub("", name, count=1)
                if strip_re:
                    name = strip_re.sub("", name)
                entries.append(Entry(file=file, code=found.group("code").strip(), name=name.strip()))
        return entries, []

    parse.label = f"named_files({file_pattern})"
    return parse


def between(parser: Parser, start: str | None = None, end: str | None = None) -> Parser:
    r"""`parser`, reading only the part of the page from `start` up to `end`.

    Both are regular expressions for a line, usually a heading: from the first
    line matching `start` (or the top of the page) up to the first line after
    it matching `end` (or the bottom of the page). For pages that also show
    signs that are not current or national: older designs, other regions.

        between(files(...), start=r"==\s*Categorisation\s*==", end=r"===\s*Obsolete\s*===")
    """
    start_re = re.compile(start, re.MULTILINE) if start else None
    end_re = re.compile(end, re.MULTILINE) if end else None

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        begin = start_re.search(wikitext) if start_re else None
        offset = begin.start() if begin else 0
        stop = end_re.search(wikitext, offset + 1) if end_re else None
        return parser(wikitext[offset : stop.start() if stop else len(wikitext)])

    parse.label = f"{_label(parser)} between {start or 'top'} and {end or 'bottom'}"
    return parse


def _label(parser: Parser) -> str:
    return getattr(parser, "label", None) or getattr(parser, "__name__", repr(parser))


def _alternatives(namespaces: tuple[str, ...]) -> str:
    return "|".join(re.escape(ns) for ns in (*namespaces, *DEFAULT_NAMESPACES))


class _Patterns:
    def __init__(self, code_pattern: str, ignore: Patterns, strip: str | None, code_prefix: str | None = None):
        prefix = f"(?:{code_prefix})" if code_prefix else ""
        # "A1 Name", "A1: Name", "A1. Name", "A1 - Name" or "A1/Name"
        self.caption = re.compile(rf"^{prefix}({code_pattern})(?:(?:[:.]|\s+[-–])?\s+|/)(.+)$")
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
