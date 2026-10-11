"""Hungary: the list of signs on the Hungarian Wikipedia (KRESZ, 1/1975 KPM-BM rendelet).

Gallery lines look like `File:Hungary road sign A-001.svg|'''A-001'''<br>Veszélyes útkanyarulat balra`;
codes are a group letter and a three-digit number: A-001, C-012, H-120.
Signs no longer in use ("Korábbi jelzések") are not read.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="hu",
    language="hu",
    country_name="Hungary",
    language_name="Hungarian",
    wiki="hu.wikipedia.org",
    page="Útjelző táblák Magyarországon",
    parser=parsers.between(
        parsers.gallery(r"[A-H]-\d{3}[a-z]?", namespaces=("Fájl", "Kép")),
        end=r"^==\s*Korábbi jelzések",
    ),
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
