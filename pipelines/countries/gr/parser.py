"""Reads the Greek list of signs: the four ΚΟΚ series, with codes in Greek letters.

Only the sections of the four series are read (Κ, Ρ, Π, Πρ), up to the
temporary signs: the later sections repeat the same codes for temporary
(yellow) versions, other and abolished signs. Captions often write a code
with Latin letters that look Greek ("K-6α", "P-33"); they are read as the
Greek ones, so every code is in one alphabet. Placeholders ("Missing image
icon…") for signs without a drawing are skipped.
"""

from __future__ import annotations

import re

from ...core import parsers
from ...core.model import Entry, Problem

_gallery = parsers.between(
    parsers.gallery(r"(?:Κ|Ρ|Π|Πρ)-\d+[α-ωά-ώ]{0,2}\d?", namespaces=("Αρχείο", "Εικόνα")),
    start=r"^===\s*Πινακίδες αναγγελίας κινδύνου",
    end=r"^===\s*Προσωρινές πινακίδες",
)
_LATIN = str.maketrans({"K": "Κ", "P": "Ρ", "a": "α", "d": "δ", "b": "β", "e": "ε", "z": "ζ", "i": "ι", "k": "κ"})
# The code at the start of a caption, after the bold marks: '''K-6α''', '''P-33''', '''Pr-4'''.
_CODE = re.compile(r"(\|\s*(?:''')?\s*)([KPΚΡΠ][rρ]?-\d+[a-zα-ωά-ώ]{0,2}\d?)")


def _greek(match: re.Match) -> str:
    code = match.group(2).replace("Pr", "Πρ").replace("Ρr", "Πρ").replace("Ρρ", "Πρ")
    series, rest = code.split("-", 1)
    return match.group(1) + series.translate(_LATIN) + "-" + rest.translate(_LATIN)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    entries, problems = _gallery(_CODE.sub(_greek, wikitext))
    # A placeholder for a sign whose drawing does not exist yet.
    return [e for e in entries if not e.file.startswith("Missing image")], problems


parse.label = "gallery (ΚΟΚ series, Greek letters)"
