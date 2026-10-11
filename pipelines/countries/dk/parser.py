"""Reads the Danish list of signs: gallery captions "A11: Farligt vejkryds, …".

A line can hold two signs where a line break is missing on the page
("D16: Valgfri passage Denmark road sign D21.svg|D21: Cykelsti"); each
image starts its own line before the gallery is read.
"""

from __future__ import annotations

import re

from ...core import parsers
from ...core.model import Entry, Problem

_gallery = parsers.gallery(r"[A-Z]\d+(?:\.\d+)*", namespaces=("Fil",))
_JOINED = re.compile(r"(?<=\S)[ \t]+(?=(?:Fil:)?Denmark road sign [^|\n]+\.svg\|)")


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    return _gallery(_JOINED.sub("\n", wikitext))
