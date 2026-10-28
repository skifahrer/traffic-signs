"""Spain: the Spanish Wikipedia's lists of signs and the English page.

Sources, in this order (a code on an earlier one keeps that one's image):

- es:Anexo:Señales de tráfico de peligro / de reglamentación / de indicación
  / de obras de España, the signs of the Catálogo oficial de señales de
  circulación (annex I of the Reglamento General de Circulación, as amended
  by Real Decreto 465/2025): P warning, R regulatory, S information and the
  roadworks signs TP, TR, TS and TB. Galleries and tables with the code and
  the name in each caption; see parser.py.
- en:Road signs in Spain, the same signs in galleries with English captions,
  for the drawings the Spanish lists lack: the lettered drawings of R-400,
  S-860, S-870, S-880 and S-890, which the Spanish lists show together in
  one row, and the newer signs P-20c, P-21b, P-22a, P-24a and P-35. The
  sections "Unofficial signs" and "Historic signs" are not read.

The Spanish names come from translations.csv (local_names="translations"):
the names of the Spanish lists, with the names of the Commons drawings for
the signs only the English page has.

Not read (IGNORE): the Spanish rows R-400, S-860, S-870, S-880 and S-890,
which show several drawings under one code (the English page has each
drawing with its own code); P-21, S-30, S-31, S-63 and R-412a, the English
page's codes for drawings the Spanish lists give as P-21a, S-30a, S-31a,
S-63a and R-412; P-1e, a sign of the English page with no Spanish name;
and S-264, S-266, S-266a, S-310, S-348b, S-354 … S-368, direction signs of
the road standard Norma 8.1-IC that the catalogue does not list.
"""

import os

from ...core import parsers
from ...core.model import Source
from .parser import parser

IGNORE = frozenset(
    "R-400 S-860 S-870 S-880 S-890 P-21 S-30 S-31 S-63 R-412a P-1e "
    "S-264 S-266 S-266a S-310 S-348b S-354 S-355 S-360 S-362 S-366 S-368".split()
)

SOURCE = Source(
    country="es",
    language="es",
    country_name="Spain",
    language_name="Spanish",
    wiki="es.wikipedia.org",
    page=[
        "Anexo:Señales de tráfico de peligro de España",
        "Anexo:Señales de tráfico de reglamentación de España",
        "Anexo:Señales de tráfico de indicación de España",
        "Anexo:Señales de tráfico de obras de España",
        "en:Road signs in Spain",
    ],
    parser=parsers.between(parser(IGNORE), end=r"^==\s*Unofficial signs\s*=="),
    local_names="translations",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
