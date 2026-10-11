"""Reads the American list of signs: gallery lines `File:MUTCD R1-1.svg|R1-1<br>Stop`.

Variants of a sign (a fluorescent or yellow version, with or without a
legend) share the MUTCD code in their captions, so the code is taken from the
image name instead ("R1-6 (yellow)"), and the name from the caption after
the code. A drawing marked "(old)" is the previous version of a sign shown
next to the current one and is skipped.
"""

from __future__ import annotations

import re

from ...core.model import Entry, Problem
from ...core.wikimedia import strip_markup

_LINE = re.compile(r"^\s*(?:File:|Image:)?\s*MUTCD[ _](?P<code>[A-Z]+\d[^|]*?)\.svg\s*\|(?P<caption>.*)$", re.IGNORECASE)
# The caption repeats the code before the name: "R1-1<br>Stop", "R2-2P<br>Truck speed limit (plaque)".
_CODE = re.compile(r"^\s*[A-Z]+\d[\w.()-]*\s*<br\s*/?>", re.IGNORECASE)


def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
    entries, problems = [], []
    in_gallery = False
    for line in wikitext.splitlines():
        if re.match(r"\s*<gallery\b", line, re.IGNORECASE):
            in_gallery = True
        elif re.match(r"\s*</gallery>", line, re.IGNORECASE):
            in_gallery = False
        elif in_gallery and (match := _LINE.match(line)) and "(old)" not in match.group("code"):
            file = f"MUTCD {match.group('code')}.svg".replace("_", " ")
            # {{abbr|HOV|High-occupancy vehicle}} reads as HOV; other templates are footnotes.
            caption = re.sub(r"\{\{abbr\|([^|}]*)\|[^{}]*\}\}", r"\1", match.group("caption"))
            if not _CODE.match(caption):
                problems.append(Problem(file, f"caption without a sign code: `{file}` → `{strip_markup(caption)}`"))
                continue
            name = strip_markup(_CODE.sub("", caption, count=1))
            entries.append(Entry(file=file, code=" ".join(match.group("code").replace("_", " ").split()), name=name))
    return entries, problems


parse.label = "gallery (MUTCD file names)"
