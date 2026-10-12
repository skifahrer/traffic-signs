"""Reads the Dutch series pages (A–F) and, for a few signs, the English page.

The six Dutch pages ("Verkeersborden in België - Serie A: Gevaarsborden", …)
list each series in a gallery, followed by the additional panels used with
it ("Gebruikte onderborden") and the abolished signs ("Historische borden").
Captions are "A1a: Gevaarlijke bocht naar links."; panels of the G series are
captioned by their type ("Type Ia: Onderbord …"), read as code GIa, and one
caption has no space after the colon ("F52:nooduitgang."). They are read up
to "Historische borden". Images in the design of the Royal Decree of 3 June
2024 ("… KB-AR 03-06-2024.svg"), which applies from 1 June 2027, are skipped:
A53, and C45, C47 and D4, which come from the English page in the current
design instead.

The English page ("Road signs in Belgium", captions "A1a: Bend to the left")
is read only for the codes in `ENGLISH`: signs the Dutch pages do not have
(the panels M4, M5, M5bis and GXI, D9b, the symbols S1–S36), show as one
sign (F51, which the English page splits into subway F51a and footbridge
F51b) or only as a photo, a PNG or in the 2027 design. Only its sections for
the current signs, "(1975-2027)", are read, not the 2027 designs or the
retired signs.

The Dutch pages skip the codes in `ENGLISH`, so no code is read from both
(the sync reports a code found with two different images as an error).
Names come from translations.csv.
"""

from __future__ import annotations

import re

from ...core import parsers
from ...core.model import Entry, Problem

CODE = r"(?:[A-FM]\d+[a-z]?\d*(?:bis)?|G[IVX]+[a-d]?|S\d+)"

# Read from the English page; the Dutch pages skip them.
ENGLISH = {
    "C45",  # Dutch page: 2027 design
    "C47",  # Dutch page: 2027 design, in three languages
    "D4",  # Dutch page: 2027 design
    "D9b",
    "F1a", "F1b", "F3a", "F3b",  # Dutch page: PNG
    "F51", "F51a", "F51b",  # Dutch page: one F51 for both, English page: F51a and F51b
    "F117",  # Dutch page: a photo
    "M4", "M5", "M5bis",
    "GXI",
    *(f"S{n}" for n in (*range(1, 6), *range(10, 22), *range(30, 37))),
}

_DUTCH = re.compile(r"\[\[Categorie:Verkeersbord in België", re.IGNORECASE)
_NEW_DESIGN = re.compile(r"^.*KB-AR 03-06-2024.*$\n?", re.MULTILINE)
_TYPE = re.compile(r"\|\s*Type ([IVX]+[a-d]?):")
_NO_SPACE = re.compile(rf"\|\s*({CODE}):(?=\S)")

_dutch = parsers.between(
    parsers.gallery(CODE, namespaces=("Bestand", "Afbeelding")),
    end=r"^===\s*Historische borden",
)
_english = parsers.between(
    parsers.gallery(CODE),
    start=r"^==\s*Warning signs \(1975-2027\)",
    end=r"^==\s*Traffic lights",
)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    if _DUTCH.search(wikitext):
        wikitext = _NEW_DESIGN.sub("", wikitext)
        wikitext = _NO_SPACE.sub(r"|\1: ", _TYPE.sub(r"|G\1:", wikitext))
        entries, problems = _dutch(wikitext)
        return [e for e in entries if e.code not in ENGLISH], problems
    entries, problems = _english(wikitext)
    return [e for e in entries if e.code in ENGLISH], problems
