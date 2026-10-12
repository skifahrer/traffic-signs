"""Sign codes written the way the Croatian list writes them: two digits after the letter.

The Croatian page and the regulations number the signs A01, B45-1, C113-2;
a drawing named "HR road sign A4.svg" is sign A04. `padded()` wraps a parser
and gives every code it reads that form, so a sign is the same code whichever
source it comes from.
"""

from __future__ import annotations

import re

from ...core.model import Entry, Parser, Problem

_CODE = re.compile(r"^([A-K])0*(\d+)(.*)$")


def normalise(code: str) -> str:
    """"A4" → "A04", "B045-1" → "B45-1", "C113-2" stays."""
    match = _CODE.match(code)
    return f"{match.group(1)}{int(match.group(2)):02d}{match.group(3)}" if match else code


def padded(parser: Parser) -> Parser:
    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        entries, problems = parser(wikitext)
        for entry in entries:
            entry.code = normalise(entry.code)
        return entries, problems

    parse.label = getattr(parser, "label", "parser")
    return parse
