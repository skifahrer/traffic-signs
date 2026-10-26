"""Slovenia: the English Wikipedia's page (Road signs in Slovenia) and the
drawings of Slovenian signs on Wikimedia Commons.

The Slovenian Wikipedia has no list of signs. Sources, in this order (a code
on an earlier one keeps that one's image):

- en:Road signs in Slovenia, galleries with English captions of the signs of
  the Pravilnik o prometni signalizaciji in prometni opremi na cestah
  (Uradni list RS, št. 46/2000) by group: I warning, II regulatory,
  III information, IV additional panels. Images are named after the sign's
  code: "Slovenia road sign I-1.1.svg", with an example value for the signs
  that take any ("Slovenia road sign II-30 (40).svg" is II-30, speed limit).
  The section "Retired signs" is not read.
- Commons, "Category:Diagrams of road signs of Slovenia", for the signs the
  page lacks: the direction and motorway signs III-84 … III-124, most
  additional panels and the road equipment VI-1 … VI-9 (barrier boards,
  traffic cones). Its subcategories of historic signs and of route signs
  are not entered.

The code is taken from the file name (parsers.files()), so captions do not
matter and the Slovenian names come from translations.csv
(local_names="translations"): the names of the 2000 rules, one name for the
drawings of a sign the rules describe together (II-45 … II-45.4 "Obvezna
smer"). The rules of 2020 renumbered the signs with four digits; Commons
has only a handful of those drawings ("SI road sign 2445 (2020).svg",
"Slovenia road sign 1119-1.svg"), so the drawings and codes of the 2000
rules are read and the four-digit files are not. The page's town signs
("Locality Sign (Slovenia).svg") have no code in the file name; Commons has
them as III-14 and III-15.
"""

import os

from ...core import parsers
from ...core.model import Source, commons_category

FILE = r"Slovenia road sign (?P<code>(?:I|II|III|IV|VI)-\d+(?:\.\d+)?)(?: \(\d+\))?\.svg"

SOURCE = Source(
    country="si",
    language="sl",
    country_name="Slovenia",
    language_name="Slovenian",
    wiki="en.wikipedia.org",
    page=[
        "Road signs in Slovenia",
        commons_category("Diagrams of road signs of Slovenia", exclude=r"(?i)historic|route signs"),
    ],
    parser=parsers.between(parsers.files(FILE), end=r"^==\s*Retired signs\s*=="),
    local_names="translations",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
