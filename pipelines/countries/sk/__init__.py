"""Slovakia: the list of signs on the Slovak Wikipedia (VL 6.1 / 6.3 / 6.4).

Gallery lines look like `Súbor:110-10 Zákruta (vľavo).svg|110-10 Zákruta (vľavo)`;
codes are three digits with optional variant parts: 101, 110-10, 240-3,5, 394-17-50.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="sk",
    language="sk",
    country_name="Slovakia",
    language_name="Slovak",
    wiki="sk.wikipedia.org",
    page="Zoznam dopravných značiek na Slovensku",
    parser=parsers.gallery(r"\d{3}(?:-[0-9]+(?:,[0-9]+)?)*", namespaces=("Súbor", "Obrázok")),
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
