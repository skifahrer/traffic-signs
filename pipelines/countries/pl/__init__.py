"""Poland: the list of signs on the Polish Wikipedia (Dz.U. 2019 poz. 2310 and later).

Gallery lines look like `Plik:PL road sign A-1.svg|'''A-1'''<br>„niebezpieczny zakręt w prawo”`;
codes are a group letter (or AT, BT, STT, ...), a number and an optional letter,
combined signs join numbers with "/": A-1, A-6a, B-3/4/10, STT-1, SB.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="pl",
    language="pl",
    country_name="Poland",
    language_name="Polish",
    wiki="pl.wikipedia.org",
    page="Wzory znaków i sygnałów drogowych w Polsce",
    parser=parsers.gallery(
        r"[A-Z]{1,3}(?:-\d+[a-z]?\d?(?:/\d+[a-z]?)*)?",
        namespaces=("Plik", "Grafika"),
        ignore=[
            r"^P-\d",  # road markings
            r"zniesion",  # abolished signs ("zniesiony", "zniesiona", "zniesiono")
            r"stanowi jedynie wariant",  # no longer a sign of its own
        ],
        strip=r"[„”]",
    ),
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
