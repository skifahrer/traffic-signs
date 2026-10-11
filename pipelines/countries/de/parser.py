"""Reads the German list of signs: its galleries, without symbols, markings and abolished signs.

- Everything before the first group of signs ("Gefahrzeichen") is symbols used
  inside signs (Sinnbilder, RWBA/RWB pictograms), not signs of their own.
- Everything after the catalogue ("Zeichen, die nicht im Verkehrszeichenkatalog
  aufgeführt wurden") is unofficial, military and railway signs.
- "Markierungen" sections are road markings, which other countries leave out too.
- "Gestrichene Zeichen" lists abolished signs in the same layout as valid ones.

Some captions write the code with an en dash ("Zeichen 501–29"); it is read as
a hyphen.
"""

from __future__ import annotations

import re

from ...core import parsers
from ...core.model import Entry, Problem

_gallery = parsers.gallery(
    r"\d{3,4}(?:\.\d)?(?:-\d{1,3}(?:,\d)?)?",
    code_prefix=r"(?:(?:Neu: )?(?:Zusatzzeichen|Zeichen) )?",
    ignore=[
        r"Zuvor: Zusatzzeichen",  # renumbered panels: "Neu: Zusatzzeichen 1001-30-800 … Zuvor: Zusatzzeichen 1001-30"
        r"wieder gestrichen",  # added in 2017 and abolished again
        r"^Zuvor:",  # the old version of a renamed sign, shown next to the new one
        r"^Sinnbild",  # symbols used inside signs
        r"^Carsharing-Plakette|^Aufkleber",  # stickers and badges, not signs
        r"Haifischzähne",  # road marking (Zeichen 342)
    ],
    # Notes on when a sign was introduced or renumbered, after the name.
    strip=r"[;,]?\s*\(?(?:(?:am|vor|seit|neu seit) \d+\.\s*\w+\.? \d{4}|\d\d\.\d\d\.\d{4}|\d{4}\)).*$"
    r"|;\s*(?:neues Zeichen|veränderte Zeichenhöhe|inhaltlich geändertes Zusatzzeichen|teils neue Nummer).*$"
    r"|\s*\(diese Nummer trug.*\)$|[;“]+$",
)

# Road markings, which other countries leave out as well.
_MARKINGS = re.compile(r"^=== Markierungen ===$.*?(?=^==)", re.MULTILINE | re.DOTALL)
_ABOLISHED = re.compile(r"^== Gestrichene Zeichen ==$.*?(?=^== )", re.MULTILINE | re.DOTALL)
# Signs that are not in the catalogue (unofficial, military, railway) follow the catalogue.
_END = re.compile(r"^== Zeichen, die nicht im Verkehrszeichenkatalog", re.MULTILINE)


# A sign shown twice, in an older and a newer drawing: the first one is used.
_DUPLICATES = {"Zeichen 533-22 Trennungstafel - ohne Gegenverkehr.svg"}


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    start = re.search(r"^== Gefahrzeichen", wikitext, re.MULTILINE)
    end = _END.search(wikitext)
    wikitext = wikitext[start.start() if start else 0 : end.start() if end else len(wikitext)]
    wikitext = _MARKINGS.sub("", _ABOLISHED.sub("", wikitext))
    wikitext = re.sub(r"(?<=\d)–(?=\d)", "-", wikitext)
    entries, problems = _gallery(wikitext)
    return [e for e in entries if e.file not in _DUPLICATES], problems


parse.label = "gallery (without abolished signs)"
