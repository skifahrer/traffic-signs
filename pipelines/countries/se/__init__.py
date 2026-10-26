"""Sweden: the Swedish Wikipedia's list of signs (Vägmärken i Sverige) and the
English page.

Sources, in this order (a code on an earlier one keeps that one's image):

- sv:Vägmärken i Sverige, galleries of the signs of Vägmärkesförordningen
  (2007:90) by group: A warning, B priority, C prohibitory, D mandatory,
  E special regulation, F–I information, J other signs, T additional panels
  and X marker boards. Images are named after the sign's code:
  "Sweden road sign A1-1.svg", with a number after the dash for the
  drawings of one sign (A1-1 left, A1-2 right; C31-7 for 70 km/h), which
  become codes of their own. Chevron boards are named after their layout:
  "SE road sign X1 (2 chevrons, left).svg". The section "Gamla vägmärken"
  (old signs) is not read.
- en:Road signs in Sweden, the same signs in galleries with English captions,
  for the drawings the Swedish page lacks (A1-2, A29-2 … A29-21, C25-2, the
  P signs, ...). The section "Historic signs" is not read.

The code is taken from the file name (parsers.files()), so captions do not
matter and the Swedish names come from translations.csv
(local_names="translations"): the names in Vägmärkesförordningen, one name
for all the drawings of a sign. Both pages also show signs in drawings named
after the numbering before 2008 ("Swedish road sign 11 13 2.svg",
"1 5 2 14 (Swedish road sign).svg") or not after a sign at all
("P-skiva skylt.png"); those have no current code in the file name and are
not read. The page's direction sign F5 is the drawing with the colours
before 2008, "Sweden road sign F5 (old colors).svg", read as F5.
"""

import os

from ...core import parsers
from ...core.model import Source

FILE = r"(?:Sweden|SE) road sign (?P<code>[A-Z]\d+(?:-\d+)*(?: \((?:\d chevrons?|temporary, \d chevrons?), (?:left|right)\))?)(?: \(old colors\))?\.svg"

SOURCE = Source(
    country="se",
    language="sv",
    country_name="Sweden",
    language_name="Swedish",
    wiki="sv.wikipedia.org",
    page=["Vägmärken i Sverige", "en:Road signs in Sweden"],
    parser=parsers.between(
        parsers.files(FILE),
        end=r"^==\s*(?:Gamla vägmärken|Historic signs)\s*==",
    ),
    local_names="translations",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
