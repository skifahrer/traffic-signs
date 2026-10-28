"""Reads the Spanish lists of signs: galleries and tables with the code in bold.

The four pages (Anexo:Señales de tráfico de peligro / reglamentación /
indicación / obras de España) show each sign in one of two layouts:

    Archivo:Spain traffic signal p11.svg|<center>'''P-11'''<br />'''Situación de un paso a nivel sin barreras'''</center><br />Peligro …
    Archivo:Spain traffic signal r101.svg|<center>'''R-101'''<br />Entrada prohibida</center>

    |-
    | <center> [[Archivo:Spain traffic signal s28.svg|150x150px]]
    | '''Zona de estancia y juego<br />S-28'''<br />Indica las zonas …

a gallery line, or a table row with the image in one cell and the text in
the next. The code is in bold, before or after the name ("P-11 Situación
…", "Zona de estancia y juego S-28"). The name is the rest of the bold text
or, when that is only the code, the plain text after it up to the end of
the centred caption. The explanation after the caption is not read. The
image is the first one of the line or row. Lines and rows without a code in
bold (photos, notes) are skipped, and so are the codes in `ignore`.

A code is read once per page, with its first drawing: R-301 (one drawing
per speed), R-200, S-12 and TS-210 have several. The Spanish list also
gives two rows the code of the row above (S-63a for the three-lane fork,
S-64a for the cycle lane next to a one-way road); those rows are dropped,
and the English page, read after it, has their drawings as S-63b and S-65a.

The English page (en:Road signs in Spain) has the same gallery layout with
English captions ("'''P-1'''<br />Intersection with priority"); its names
are not used, as Source.local_names is "translations".
"""

from __future__ import annotations

import re

from ...core.model import Entry, Problem

CODE = re.compile(r"\b((?:TP|TR|TS|TB|TM|TL|[PRS])-\d+[a-z]?(?:-\d+)?)\b")
_FILE = re.compile(r"(?:^|\[\[|\|)\s*(?:Archivo|File|Imagen|Image)?\s*:?\s*([^|\[\]:]+?\.(?:svg|png|jpe?g))\s*(?=[|\]])", re.IGNORECASE)
_BOLD = re.compile(r"'''(.*?)'''", re.DOTALL)


def _plain(text: str) -> str:
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"<[^>]+>|\{\{[^}]*\}\}|''", "", text)
    return " ".join(text.split())


def _items(wikitext: str):
    """Gallery lines and table rows, one string each."""
    for block in re.split(r"^\s*\|-.*$|</?gallery[^>]*>", wikitext, flags=re.MULTILINE):
        if block.lstrip().startswith(("|", "!")) or "\n|" in block:
            yield block  # a table row: its cells, the image and the text
        else:
            yield from block.splitlines()  # gallery lines


def parser(ignore: frozenset[str] = frozenset()):
    """A parser for the Spanish and English pages that skips the codes in `ignore`."""

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        entries, problems, seen = [], [], set()
        for item in _items(wikitext):
            image = _FILE.search(item)
            if not image:
                continue
            caption = item[image.end():]
            bolds = _BOLD.findall(caption)
            bold = " ".join(_plain(b) for b in bolds)
            code = CODE.search(bold)
            if not code or code.group(1) in ignore or code.group(1) in seen:
                continue
            seen.add(code.group(1))
            file = " ".join(image.group(1).replace("_", " ").split())
            name = " ".join((bold[: code.start()] + " " + bold[code.end():]).split()).strip(" :.-–")
            if not name:  # '''R-101'''<br />Entrada prohibida</center>
                rest = caption.split("'''", 2)[-1] if len(bolds) == 1 else ""
                name = _plain(re.split(r"</center>|\n", rest)[0]).strip(" :.-–")
            if not name:
                problems.append(Problem(file=file, message=f"{code.group(1)}: no name"))
                continue
            entries.append(Entry(file=file, code=code.group(1), name=name))
        return entries, problems

    parse.label = "es.parser"
    return parse
