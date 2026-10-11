"""Reads the Austrian list of signs: one gallery block per paragraph of the StVO.

Austria has no catalogue numbers: a sign is cited by its paragraph and number
("§ 50 Z 1" is Gefahrenzeichen 1), and the numbers start again in every
paragraph. Captions give only the number ("1: Querrinne oder Aufwölbung"),
so the code is built from the paragraph heading the gallery is under:
"§50 Z1", "§52 Z4a", "§53 Z17", and "§54 a" for the additional plates.
Variants that share a number get what their image name adds after it:
"Vorschriftszeichen 15 links abb.svg" is "§52 Z15 (links abb)".
The sections after § 54 (railway crossings, historic signs) are not read.
"""

from __future__ import annotations

import re
from collections import Counter

from ...core import parsers
from ...core.model import Entry, Problem

_gallery = parsers.gallery(
    r"\d+[a-z]?(?:-[a-z])?|[a-z]",
    namespaces=("Datei", "Bild"),
    strip=r"^(?:[a-z]|groß|klein|hoch|quer):\s*",  # "13c a: …", "13a groß: …": the variant, already in the code
)
_SECTION = re.compile(r"^==\s*§\s*(\d+)\.[^=]*==\s*$", re.MULTILINE)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    entries, problems = [], []
    headings = list(_SECTION.finditer(wikitext))
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else wikitext.find("\n== ", heading.end())
        paragraph = heading.group(1)
        found, found_problems = _gallery(wikitext[heading.end() : end if end >= 0 else len(wikitext)])
        counts = Counter(e.code for e in found)
        for entry in found:
            variant = _variant(entry.file, entry.code) if counts[entry.code] > 1 else ""
            number = f"{entry.code} ({variant})" if variant else entry.code
            entry.code = f"§{paragraph} {number}" if paragraph == "54" else f"§{paragraph} Z{number}"
        entries += found
        problems += found_problems
    return entries, problems


def _variant(file: str, number: str) -> str:
    """What the image name adds after the number: "Vorschriftszeichen 15 links abb.svg" → "links abb"."""
    stem = re.sub(r"\s*\(\d{4}\)", "", file.rsplit(".", 1)[0])
    match = re.search(rf"\b{re.escape(number)}\b[\s-]*(.*)$", stem)
    return match.group(1).strip() if match else ""


parse.label = "gallery per StVO paragraph"
