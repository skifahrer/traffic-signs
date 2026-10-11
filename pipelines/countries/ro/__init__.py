"""Romania: the list of signs on the Romanian Wikipedia (Indicatoarele rutiere din România).

Rows of wikitables, an image and the sign's name in bold; codes come from the
images' file names (see parser.py): A warning, B priority, C prohibition,
D mandatory, E/F orientation, G information, T and P additional panels.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="ro",
    language="ro",
    country_name="Romania",
    language_name="Romanian",
    wiki="ro.wikipedia.org",
    page="Indicatoarele rutiere din România",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
