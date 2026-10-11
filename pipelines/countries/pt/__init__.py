"""Portugal: the list of signs on the Portuguese Wikipedia (Sinalização de trânsito em Portugal, RST).

Gallery captions are "A1a - Curva à direita: indicação da existência de uma
curva perigosa à direita": code, name, then a description after the colon,
which is left out of the name; see parser.py.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="pt",
    language="pt",
    country_name="Portugal",
    language_name="Portuguese",
    wiki="pt.wikipedia.org",
    page="Sinalização de trânsito em Portugal",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
