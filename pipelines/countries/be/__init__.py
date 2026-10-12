"""Belgium: the Dutch Wikipedia's lists of signs, one page per series (A–F), and the English page for the rest.

The signs of the Wegcode (Royal Decree of 1 December 1975) are listed on six
Dutch pages, "Verkeersborden in België - Serie A: Gevaarsborden" to "… Serie
F: Aanwijzingsborden". Gallery captions are "A1a: Gevaarlijke bocht naar
links."; the additional panels used with each series follow under "Gebruikte
onderborden", the M series by code and the G series by type ("Type Ia:
Onderbord …", read as GIa). A panel shown on more than one page counts once.
The abolished signs ("Historische borden": C48, C49, F1, F3, F107, F109,
F113) and the drawings for the Royal Decree of 3 June 2024, which applies
from 1 June 2027 ("… KB-AR 03-06-2024.svg"), are not read.

The English page, "Road signs in Belgium", adds what the Dutch pages lack or
show only as one sign, a photo, a PNG or in the 2027 design: the panels M4,
M5, M5bis and GXI, D9b, the subway and footbridge F51a/F51b, C45, C47, D4,
F1a/F1b, F3a/F3b, F117 and the symbols S1–S36 used on direction signs. Only
its sections for the current signs, "(1975-2027)", are read. See parser.py
for which page each sign comes from.

The captions on the Dutch pages are long descriptions and the English page
has English ones, so the Dutch names (nl-BE, next to the Netherlands' nl)
come from translations.csv. Variants that share a code (C43 30 and 50, D1b
and D4 by direction, E9a with a symbol, F1a–F3b horizontal and vertical,
examples of the G panels) and the panels without a code in their caption
(GXa–GXd, the paid-parking panels) get codes in corrections.csv.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="be",
    language="nl",
    country_name="Belgium",
    language_name="Dutch",
    wiki="nl.wikipedia.org",
    page=[
        "Verkeersborden in België - Serie A: Gevaarsborden",
        "Verkeersborden in België - Serie B: Voorrangsborden",
        "Verkeersborden in België - Serie C: Verbodsborden",
        "Verkeersborden in België - Serie D: Gebodsborden",
        "Verkeersborden in België - Serie E: Parkeren- en stilstaanborden",
        "Verkeersborden in België - Serie F: Aanwijzingsborden",
        "en:Road signs in Belgium",
    ],
    parser=parse,
    local_names="translations",
    names_key="nl-BE",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
