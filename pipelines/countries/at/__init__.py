"""Austria: the list of signs on the German Wikipedia (StVO 1960, §§ 50–54).

Gallery lines look like `Gefahrenzeichen 1.svg|1: Querrinne oder Aufwölbung`;
the code adds the paragraph to the number (see parser.py): §50 Z1, §52 Z4a,
§53 Z17, §54 a. Names are German, kept under "de-AT" next to Germany's "de".
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="at",
    language="de",
    country_name="Austria",
    language_name="German",
    wiki="de.wikipedia.org",
    page="Bildtafel der Verkehrszeichen in Österreich",
    parser=parse,
    names_key="de-AT",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
