"""France: the signs on the French Wikipedia's articles and lists of road signs, one per family.

Each family (danger, priorité, prescription, indication, services, temporaire)
has an article and some a list ("Liste des signaux routiers de … en France");
both are read, and a sign shown on both counts once. Captions differ in layout
from page to page and often have no name, but the images are named after the
sign: "France road sign A1a.svg". The code comes from that name, and the
French names from translations.csv.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="fr",
    language="fr",
    country_name="France",
    language_name="French",
    wiki="fr.wikipedia.org",
    page=[
        "Panneau de signalisation routière de danger en France",
        "Panneau de signalisation routière de priorité en France",
        "Panneau de signalisation routière de prescription en France",
        "Panneau de signalisation routière d'indication en France",
        "Panneau de signalisation routière de services en France",
        "Panneau de signalisation routière temporaire en France",
        "Liste des signaux routiers de danger en France",
        "Liste des signaux routiers de prescription en France",
        "Liste des signaux routiers d'indication en France",
        "Liste des signaux routiers de services en France",
    ],
    parser=parsers.files(
        r"(?i:France road sign) (?P<code>[A-Z]+\d.*)\.(?:svg|png)",
        ignore=[
            r"ancien",  # the previous drawing of a sign, shown next to the current one
            r"^France Road Sign A6\.svg$",  # the same sign as "France road sign A6.svg"
        ],
    ),
    local_names="translations",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
