"""Reads the tables of et:"Eesti liiklusmärgid".

Each table has the columns Märk (code), Pilt (image), Nimi (name) and
Tähendus (meaning). Variants of a sign share the code and the name through
`rowspan`: 133 spans the rows of 133a, 133b and 133c, 623a the rows of
623a1 to 623a6, and a few rows show two images in one cell (537ak and its
second panel 537ak2, 559c1 and 559c2). So the name is taken from the table,
following its rowspans, and the code from the image's file name
("Estonia road sign 133b.svg" → 133b), which tells the variants apart.
Where the file name gives a value in brackets ("351(30)", "351(70)m": an
example value on a sign that takes any), the code is the table's (351,
351m).
"""

from __future__ import annotations

import re

from ...core.model import Entry, Problem
from ...core.wikimedia import strip_markup

_IMAGE = re.compile(r"\[\[\s*(?:Fail|File|Pilt|Image)\s*:\s*([^|\]]+)", re.IGNORECASE)
_FILE_CODE = re.compile(r"Estonia road sign (?P<code>.+)\.svg", re.IGNORECASE)
_CODE = re.compile(r"\d{3}[a-z]{0,2}\d?")
_ROWSPAN = re.compile(r'rowspan\s*=\s*"?(\d+)', re.IGNORECASE)
_QUOTES = " „“”\"'"


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    entries: list[Entry] = []
    problems: list[Problem] = []
    for table in re.finditer(r"^\{\|.*?^\|\}", wikitext, flags=re.MULTILINE | re.DOTALL):
        spans: dict[int, tuple[int, str]] = {}  # column -> (rows still to cover, cell)
        for row in re.split(r"^\s*\|-.*$", table.group(0), flags=re.MULTILINE)[1:]:
            columns = _columns(_cells(row), spans)
            if not columns:
                continue
            table_code = strip_markup(columns.get(0, "")).strip()
            name = strip_markup(columns.get(2, "")).strip(_QUOTES)
            for image in _IMAGE.findall(columns.get(1, "")):
                file = " ".join(image.replace("_", " ").split())
                match = _FILE_CODE.fullmatch(file)
                code = match.group("code") if match else ""
                if not _CODE.fullmatch(code):
                    code = table_code
                if not _CODE.fullmatch(code) or not name:
                    problems.append(Problem(file, f"row without a sign code or name: `{file}` → `{table_code} {name}`"))
                    continue
                entries.append(Entry(file=file, code=code, name=name))
    return entries, problems


def _cells(row: str) -> list[tuple[str, int]]:
    """The data cells of one table row, each with its rowspan."""
    cells = []
    for line in row.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith(("|}", "|+", "|-")):
            continue
        for cell in line[1:].split("||"):
            attributes, bar, content = cell.partition("|")
            span = 1
            if bar and "[[" not in attributes and "=" in attributes:
                found = _ROWSPAN.search(attributes)
                span = int(found.group(1)) if found else 1
                cell = content
            cells.append((cell.strip(), span))
    return cells


def _columns(cells: list[tuple[str, int]], spans: dict[int, tuple[int, str]]) -> dict[int, str]:
    """The row's cells by column, with the cells that rows above span into it."""
    columns: dict[int, str] = {}
    if not cells:
        return columns
    column, index = 0, 0
    while index < len(cells) or column in spans:
        if column in spans:
            left, value = spans[column]
            columns[column] = value
            if left <= 1:
                del spans[column]
            else:
                spans[column] = (left - 1, value)
        else:
            value, span = cells[index]
            index += 1
            columns[column] = value
            if span > 1:
                spans[column] = (span - 1, value)
        column += 1
    return columns
