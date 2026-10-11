"""Finland: the lists of signs on the Finnish Wikipedia, one per sign family (2020 reform).

Each list starts with the current signs ("Nykyiset …"), then the signs of
earlier years ("Vuosina 1994–2020", …); only the current section is read.
Gallery lines look like `Kuva:Finland road sign A1.1.svg|A1.1. Mutka`; codes
are a letter and a number with an optional variant: A1.1, C32, H22.1.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="fi",
    language="fi",
    country_name="Finland",
    language_name="Finnish",
    wiki="fi.wikipedia.org",
    page=[
        "Luettelo Suomen liikenteen varoitusmerkeistä",
        "Luettelo Suomen liikenteen etuajo-oikeus- ja väistämismerkeistä",
        "Luettelo Suomen liikenteen kielto- ja rajoitusmerkeistä",
        "Luettelo Suomen liikenteen määräysmerkeistä",
        "Luettelo Suomen liikenteen sääntömerkeistä",
        "Luettelo Suomen liikenteen opastusmerkeistä",
        "Luettelo Suomen liikenteen palvelukohteiden opastusmerkeistä",
        "Luettelo Suomen liikenteen lisäkilvistä",
    ],
    parser=parsers.between(
        parsers.gallery(r"[A-I]\d+(?:\.\d+)?", namespaces=("Kuva", "Tiedosto")),
        start=r"^==\s*Nykyiset",
        end=r"^==(?!=)",
    ),
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
