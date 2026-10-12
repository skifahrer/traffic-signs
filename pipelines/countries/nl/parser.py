"""Reads the gallery captions of both pages: "A1: Maximumsnelheid (1)" on the
Dutch one, "A1: Speed limit (50 km/h)" on the English one.

The Dutch page is read from the top up to "Contrasterende bies", which
repeats B6, C1, C2, E1 and E2 with and without their white border. The
sections after it show temporary detour signs, bilingual Frisian signs, toll
and local signs, and the environmental-zone signs C22a–C22d that C22e
replaced in 2025.

The English page is read from the top up to "Toll Road": the series A–L,
which add K5, K6, K12–K14 and a few signs from outside the RVV (BB01, BB13,
BB23-1 to -3, L51, L403), the temporary signs (only the U-route signs BW501
and BW501e have a code) and the bilingual Frisian signs, of which only the
Dutch-only "C2f + OB705" is read. Toll, fatbike and retired signs follow.
The lead image (L401, national speed limits at the border) stands outside
the galleries and is read by its file name.

Before reading, captions are made regular: "C22e1 (onderbord): …" and
"C22e1 (sub-panel): …" become "C22e1: …", {{nowrap|…}} keeps its text and
galleries that follow each other on one line ("</gallery><gallery>") are
split. The names come from translations.csv (see __init__.py), so what the
captions say after the code only matters in the logs; the number a sign had
in the RVV 1966 ("(81a)") and the explanation after a full stop are
stripped from it. Variants that share a code (K2 and K4 in the 2010 design,
L19 left and right, F10 for customs) get codes of their own in
corrections.csv.
"""

from __future__ import annotations

import re

from ...core import parsers
from ...core.model import Entry, Problem

_CODE = r"[A-L]\d+[a-z]?\d*(?:-\d+)?(?: \+ OB\d+)?|BB\d+(?:-\d+)?|BW\d+e?"
_gallery = parsers.between(
    parsers.gallery(
        _CODE,
        namespaces=("Bestand",),
        ignore=[
            # English page: the temporary diversion signs without a code
            r"^(?:Diversion announcement|Follow the indicated direction|Announcement of diversion)\b",
            # English page: the Frisian versions of BB01, C2f + OB705, G13, OB54 and a place name
            r"\b[Bb]i-?lingual\b",
        ],
        strip=r"\s*\((?:\d+[a-z]?(?:,\s*[a-z\d]+)*|\d+, ook bij stijgingen)\)\s*$|\.\s.*$|\.$",
    ),
    end=r"^==\s*(?:Contrasterende bies|Toll Road)\s*==",
)
_lead = parsers.files(r"NL verkeersbord (?P<code>L4\d\d)\.svg")
_PANEL = re.compile(r"(\|\s*[A-L]\d+[a-z]?\d*)\s+\((?:onderbord|sub-panel)\):")
_NOWRAP = re.compile(r"\{\{nowrap\|([^{}|]*)\}\}", re.IGNORECASE)
_JOINED = re.compile(r"</gallery>\s*<gallery>", re.IGNORECASE)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    wikitext = _JOINED.sub("</gallery>\n<gallery>", wikitext)
    wikitext = _PANEL.sub(r"\1:", _NOWRAP.sub(r"\1", wikitext))
    entries, problems = _gallery(wikitext)
    seen = {(entry.file, entry.code) for entry in entries}
    entries += [entry for entry in _lead(wikitext)[0] if (entry.file, entry.code) not in seen]
    return entries, problems
