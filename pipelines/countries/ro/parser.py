"""Reads the Romanian list of signs: wikitables with the image in one cell and the bold name in the next.

    |align="center"|[[Fișier:RO A1.svg|100x100px]]
    |align="center"|'''Curbă la stânga'''

The page gives no sign codes, so the code is read from the name of the
row's first image, as Commons names them: "RO road sign A10.svg",
"Romania road sign A7.svg", "RO A13.svg",
"RomanianTrafficSign C01-NoEntry 2011.svg" → A10, A7, A13, C01. Rows whose
image has no code (a few drawings) are reported; road number plates are skipped, so
corrections.csv can add the signs among them. Only the sections of signs are
read, up to "Context".
"""

from __future__ import annotations

import re

from ...core.model import Entry, Problem
from ...core.wikimedia import strip_markup

_FILE = re.compile(r"\[\[\s*(?:Fișier|File|Imagine|Image)\s*:\s*([^|\]]+?)\s*[|\]]", re.IGNORECASE)
_NAME = re.compile(r"'''(.+?)'''")
_CODE = re.compile(r"^(?:RO road sign|Romania road sign|Romanian road sign|RomanianTrafficSign|RO)\s+([A-Z]\d+[a-z]?(?:-\d+)?)\b")
# Road number plates (DJ703B, E70, A3, …) are not signs.
_ROAD_NUMBER = re.compile(r"^(?:RO Roadsign \d+|[A-Z]{1,2}\d+[A-Z]?-RO)\.svg$")
_END = re.compile(r"^==\s*Context", re.MULTILINE)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    end = _END.search(wikitext)
    entries, problems = [], []
    for row in wikitext[: end.start() if end else None].split("\n|-"):
        file = _FILE.search(row)
        name = _NAME.search(row[file.end() :]) if file else None
        if not file or not name:
            continue
        if _ROAD_NUMBER.match(file.group(1)):
            continue
        code = _CODE.match(file.group(1))
        if code:
            entries.append(Entry(file=file.group(1), code=code.group(1), name=strip_markup(name.group(1)).strip()))
        else:
            problems.append(Problem(file=file.group(1), message=f"no sign code in the file name: {file.group(1)}"))
    return entries, problems
