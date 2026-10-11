"""Germany: the list of signs on the German Wikipedia (VwV-StVO, catalogue of 2017 and later).

Gallery lines look like `Zeichen 101 - Gefahrstelle, StVO 1970.svg|'''Zeichen 101'''<br />[[Gefahr]]stelle`;
codes are the number from the catalogue of traffic signs, with an optional
variant after a dot or hyphen: 101, 101-11, 274.1, 1000-10. Additional
panels ("Zusatzzeichen") have four-digit numbers.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="de",
    language="de",
    country_name="Germany",
    language_name="German",
    wiki="de.wikipedia.org",
    page="Bildtafel der Verkehrszeichen in der Bundesrepublik Deutschland seit 2017",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
