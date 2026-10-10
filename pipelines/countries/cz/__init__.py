"""Czechia: the list of signs on the Czech Wikipedia (vyhláška 294/2015 Sb. and later).

Table rows look like `| [[Soubor:…svg|120px]] || A 1a '''Zatáčka vpravo''' || …`;
codes are a 1–3 letter group, a number and an optional letter: A 1a, IP 10b-c, ZPI 1.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="cz",
    language="cs",
    country_name="Czechia",
    language_name="Czech",
    wiki="cs.wikipedia.org",
    page="Seznam dopravních značek v Česku",
    parser=parsers.wikitable(
        r"[A-Z]{1,3} \d+[a-z]?(?:-[a-z])?",
        namespaces=("Soubor", "Obrázek"),
        ignore=[
            r"^\d{3} ",  # symbols used inside signs (101 Zámek, 201 Moped, ...)
            r"^[a-zěščřžýáíéúůó(]",  # photos of devices without a code (odrazky, svodidla, ...)
            r"^V \d",  # road markings
            r"^Návěst pro cyklisty$",  # no code on the page
            r"^IP (8|14|15|25|26|27)[ab] ",  # renumbered to IZ by 294/2015 Sb.
            r"30/2001 Sb\.$",  # versions from the previous decree, replaced by 294/2015 Sb.
            r"^IJ 15 Dopravní vysílání",  # abolished in 2016; the code now means another sign
        ],
        strip=r"\s*\d+/\d{4} Sb\.$|\s*\(do \d+\. \d+\. \d{4} chybně.*\)$|\.$",
    ),
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
