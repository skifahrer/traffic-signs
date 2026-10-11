"""Reads the Portuguese list of signs: gallery captions "A1a - Curva à direita: indicação …".

Only the current list is read ("Lista de sinais"), not the history before it.
The name ends at the colon; the description after it is left out. Before
reading, captions are made regular: additional panels are written
"Modelo 1a — Distância", and become code M1a (the code in their image
names); "G2b- …" and "G5a— …" get the usual " - "; a caption for several
signs ("F1a, F1b e F1c — …") keeps the first code. Signs without a drawing
(a question mark image) are skipped.
"""

from __future__ import annotations

import re

from ...core import parsers
from ...core.model import Entry, Problem

_gallery = parsers.between(
    parsers.gallery(r"[A-Z]\d+[a-z]?\d?", namespaces=("Ficheiro", "Arquivo", "Imagem"), strip=r"\s*[:;].*$"),
    start=r"^==\s*Lista de sinais",
)
_PANEL = re.compile(r"\|\s*Modelos?\s+(\d+[a-z]?)\b")
_DASH = re.compile(r"(\|\s*[A-Z]\d+[a-z]?\d?)\s*[—–-]\s*")
# "F1a, F1b e F1c — …", "M8a e 8b — …": a caption for several signs keeps the first code.
_LIST = re.compile(r"(\|\s*[A-Z]\d+[a-z]?\d?)(?:(?:\s*,\s*|\s+e\s+)[A-Z]?\d*[a-z]\d?\b)+")


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    wikitext = _LIST.sub(r"\1", _PANEL.sub(r"|M\1", wikitext))
    entries, problems = _gallery(_DASH.sub(r"\1 - ", wikitext))
    # Signs without a drawing yet have a question mark as their image.
    return [e for e in entries if not e.file.startswith("Question mark")], problems
