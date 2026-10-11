"""Reads the Ukrainian list of signs: wikitables of number, image, name and description.

    |-
    |1.3.1
    |[[Файл:Ukraine road sign 1.3.1.svg|60px]]
    | rowspan="2" |Декілька поворотів
    |-
    |1.3.2
    |[[Файл:UA road sign 1.3.2.svg|60px]]

A name spanning several rows (rowspan) names each of their signs; in those
rows the next cell is already the description.
"""

from __future__ import annotations

import re

from ...core.model import Entry, Problem
from ...core.wikimedia import strip_markup

_CODE = re.compile(r"^\d+\.\d+(?:\.\d+)*$")
_FILE = re.compile(r"\[\[\s*(?:Файл|File|Зображення|Image)\s*:\s*([^|\]]+?)\s*[|\]]", re.IGNORECASE)
_ROWSPAN = re.compile(r'^\s*rowspan\s*=\s*"?(\d+)"?\s*\|(.*)$')


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    entries, problems = [], []
    name, left = "", 0  # a name spanning rows, and how many rows it still covers
    for row in re.split(r"^\|-.*$", wikitext, flags=re.MULTILINE):
        cells = [line[1:] for line in row.splitlines() if line.startswith("|") and not line.startswith(("|}", "|+"))]
        if len(cells) < 2 or not _CODE.match(cells[0].strip()):
            continue
        code, image = cells[0].strip(), _FILE.search(cells[1])
        if left <= 0:  # the name column has a cell in this row (else a spanning name covers it)
            span = _ROWSPAN.match(cells[2]) if len(cells) > 2 else None
            name, left = (strip_markup(span.group(2)).strip(), int(span.group(1))) if span else (strip_markup(cells[2]).strip() if len(cells) > 2 else "", 1)
        left -= 1
        if not image:
            problems.append(Problem(file="", message=f"{code}: no image"))
        elif not name:
            problems.append(Problem(file=image.group(1), message=f"{code}: no name"))
        else:
            entries.append(Entry(file=image.group(1), code=code, name=name))
    return entries, problems
