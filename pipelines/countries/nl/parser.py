"""Reads the Dutch list of signs: gallery captions "A1: Maximumsnelheid (1)".

Only the signs of the RVV 1990 are read: from the top of the page up to
"Contrasterende bies", which repeats B6, C1, C2, E1 and E2 with and without
their white border. The sections after it show temporary detour signs,
bilingual Frisian signs, toll and local signs, and the environmental-zone
signs C22a–C22d that C22e replaced in 2025.

Before reading, captions are made regular: "C22e1 (onderbord): …" becomes
"C22e1: …", {{nowrap|…}} keeps its text and galleries that follow each other
on one line ("</gallery><gallery>") are split. The number a sign had in the
RVV 1966, in brackets at the end of a caption ("(81a)", "(16, 62)"), is not
part of the name; nor is the explanation after a full stop ("Stop. In het
bord kan worden aangegeven …"). Variants that share a code (K2 and K4 in the
2010 design, L19 left and right, F10 for customs) get codes of their own in
corrections.csv.
"""

from __future__ import annotations

import re

from ...core import parsers
from ...core.model import Entry, Problem

_gallery = parsers.between(
    parsers.gallery(
        r"[A-L]\d+[a-z]?\d*(?:-\d+)?",
        namespaces=("Bestand",),
        strip=r"\s*\((?:\d+[a-z]?(?:,\s*[a-z\d]+)*|\d+, ook bij stijgingen)\)\s*$|\.\s.*$|\.$",
    ),
    end=r"^==\s*Contrasterende bies",
)
_PANEL = re.compile(r"(\|\s*[A-L]\d+[a-z]?\d*)\s+\(onderbord\):")
_NOWRAP = re.compile(r"\{\{nowrap\|([^{}|]*)\}\}", re.IGNORECASE)
_JOINED = re.compile(r"</gallery>\s*<gallery>", re.IGNORECASE)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    wikitext = _JOINED.sub("</gallery>\n<gallery>", wikitext)
    wikitext = _PANEL.sub(r"\1:", _NOWRAP.sub(r"\1", wikitext))
    return _gallery(wikitext)
