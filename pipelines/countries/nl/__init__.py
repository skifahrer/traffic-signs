"""Netherlands: the list of signs on the Dutch Wikipedia (Verkeersborden in Nederland, RVV 1990).

Gallery captions are "A1: Maximumsnelheid (1)": code, name, and in brackets
the number the sign had in the RVV 1966, which is left out of the name. Only
the series A–L of the RVV 1990 are read, not the older and local signs further
down the page; see parser.py.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="nl",
    language="nl",
    country_name="Netherlands",
    language_name="Dutch",
    wiki="nl.wikipedia.org",
    page="Verkeersborden in Nederland",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
