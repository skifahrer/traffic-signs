"""Latvia: the Latvian Wikipedia's list of signs (Latvijas ceļa zīmes), the
English page and the drawings of current signs on Wikimedia Commons.

Sources, in this order (a code on an earlier one keeps that one's image):

- lv:Latvijas ceļa zīmes, the signs of annex 4 of the Road Traffic
  Regulations (Ceļu satiksmes noteikumi, LVS 77-1:2016) in eight tables:
  number, image, name. Images are named after the sign's number:
  "LV road sign 101.svg", "Latvia road sign 133.svg", "Lv404.svg", with a
  capital letter for the drawings of one number that differ (701A–701D,
  704A/704B, 706A/706B, 707B), which become codes of their own.
- en:Road signs in Latvia, the same signs in galleries with English captions,
  for 754 (advance notice of an expressway exit) and the vertical markings
  905–907 that the Latvian page lacks. Only the current signs are read: the
  section "Historic signs" (the 1938 signs) is skipped.
- Commons, "Category:Diagrams of road signs of Latvia", for the vertical
  markings 901–909 of annex 5 (chevron and direction boards, road works
  barriers), which no page shows complete. Its subcategories of historic and
  Soviet signs and of road number plates are not entered.

The code is taken from the file name (parsers.files()), so captions do not
matter and the Latvian names come from translations.csv
(local_names="translations"); for the signs on the Latvian page they are
its captions, for the others the names in the regulations. The Latvian
page shows the road number plates 740–742 in the wrong rows (the drawing
named 740 is the red main road plate, 741, and so on); corrections.csv gives
each drawing the number the regulations give it. Not read:
"Latvia road sign 524A.svg" (end of the customs zone, a sign of the 2011
numbering, no longer in the regulations), "LV road sign 535a.svg" and
"536a.svg" (the pedestrian crossing signs on a fluorescent board, the same
signs 535 and 536) and "Latvia road sign 734C.svg" (a lane change sign
that is not in the regulations); local road numbers ("V1035-LV.svg") have no
sign code in the file name.
"""

import os

from ...core import parsers
from ...core.model import Source, commons_category

FILE = r"(?:Latvia(?:n)? road sign|LV road sign|Lv|Ceļa zīme)[ -]?(?P<code>\d{3}(?:\.\d)?[A-Za-z]?)(?: \([^)]*\))?\.(?:svg|png)"

SOURCE = Source(
    country="lv",
    language="lv",
    country_name="Latvia",
    language_name="Latvian",
    wiki="lv.wikipedia.org",
    page=[
        "Latvijas ceļa zīmes",
        "en:Road signs in Latvia",
        commons_category(
            "Diagrams of road signs of Latvia",
            exclude=r"(?i)historic|soviet|road number|route signs|european road|motorway number",
        ),
    ],
    parser=parsers.between(
        parsers.files(FILE, ignore=r" (?:524A|535a|536a|734C)\.svg$"),
        end=r"^==\s*Historic signs\s*==",
    ),
    local_names="translations",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
