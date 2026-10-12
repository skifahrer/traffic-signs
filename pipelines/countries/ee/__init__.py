"""Estonia: the list of signs on the Estonian Wikipedia (Eesti liiklusmärgid).

The page lists the signs of the regulation "Liiklusmärkide ja teemärgiste
tähendused ning nõuded fooridele" (2011) in tables of four columns: code (Märk),
image (Pilt), name (Nimi) and meaning (Tähendus). Variants share the code
and name cells through rowspans (133 for 133a–133c, 623a for 623a1–623a6),
so the parser follows the rowspans for the name and takes the code from
the image's file name, "Estonia road sign 133b.svg"; see parser.py. All
536 images are SVG drawings on Commons.

The page names both 141 and 142 "Ohtlik kurv vasakule"; corrections.csv
gives 141, the bend to the right, its name.

The English page, "Road signs in Estonia", is not read: the only signs it
shows that the Estonian page lacks are zone signs numbered 382–394 and 386
(four of them PNG drawings), which the current regulation does not list
on their own; it has the zone signs 381–398 ("Üks mõjuala" …) with the
restriction drawn in.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="ee",
    language="et",
    country_name="Estonia",
    language_name="Estonian",
    wiki="et.wikipedia.org",
    page="Eesti liiklusmärgid",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
