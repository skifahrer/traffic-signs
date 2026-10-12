"""Reads the Bulgarian list of signs: wikitables of code, image, name and explanation.

    |-
    | style="text-align:center;" |А1
    | style="text-align:center;" |[[Файл:BG road sign А1.svg|100px]]
    |Опасен завой надясно
    | rowspan=4 | Опасен е завоят ...

The code is the one in the first cell, as the regulation writes it, with
Cyrillic letters (А1, Г14а, Ж20.1, Т18.2). The image is the first one in the
second cell: a row that shows several drawings of one sign (the green,
blue and white boards of Д1, Ж1 or Ж14, the left and right countdown markers
А35.1) is one sign, with the drawing the page shows first. Images in the
explanation cell (an older drawing, a related sign) are not read. Rows
without code and image (notes on withdrawn numbers) are skipped. The image
of a row is used whatever its file is called: Д28 (park and ride) is drawn
in "BG road sign Д27.svg", a P+T board named after the sign before it.

A code typed with Latin letters that look like Cyrillic ones ("E21" for
Е21, "Д10a" for Д10а, as in some file names on Commons) is read as the
Cyrillic code (`cyrillic()`), so one sign does not become two codes.
"""

from __future__ import annotations

import re

from ...core.model import Entry, Problem
from ...core.parsers import _cells
from ...core.wikimedia import strip_markup

# Latin letters that look like Cyrillic ones, as they turn up in typed codes.
_LOOKALIKES = str.maketrans("ABCEHKMOPTXaceopx", "АВСЕНКМОРТХасеорх")
_CODE = re.compile(r"^[АБВГДЕЖТ]\d+(?:\.\d+)?[а-я]?$")
_FILE = re.compile(r"\[\[\s*(?:Файл|Картинка|File|Image)\s*:\s*([^|\]]+?)\s*[|\]]", re.IGNORECASE)


def cyrillic(code: str) -> str:
    """The code with Latin look-alike letters made Cyrillic: "E21" → "Е21", "Д10a" → "Д10а"."""
    return " ".join(code.split()).translate(_LOOKALIKES)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    entries, problems = [], []
    for row in re.split(r"^\s*\|-.*$", wikitext, flags=re.MULTILINE):
        cells = _cells(row)
        if len(cells) < 2:
            continue
        code, image = cyrillic(strip_markup(cells[0])), _FILE.search(cells[1])
        if not image:
            if code:
                problems.append(Problem(file="", message=f"{code}: no image"))
            continue
        file = " ".join(image.group(1).replace("_", " ").split())
        name = strip_markup(cells[2]).strip().rstrip(".") if len(cells) > 2 else ""
        if not _CODE.match(code):
            problems.append(Problem(file=file, message=f"row without a sign code: `{file}` → `{code}`"))
        elif not name:
            problems.append(Problem(file=file, message=f"{code}: no name"))
        else:
            entries.append(Entry(file=file, code=code, name=name))
    return entries, problems
