"""Ukraine: the list of signs on the Ukrainian Wikipedia (Дорожні знаки України, ДСТУ 4100).

Wikitables with the sign number (1.1, 5.20.2, 7.1.1), its image and its name;
see parser.py.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="ua",
    language="uk",
    country_name="Ukraine",
    language_name="Ukrainian",
    wiki="uk.wikipedia.org",
    page="Дорожні знаки України",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
