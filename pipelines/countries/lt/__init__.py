"""Lithuania: the Lithuanian Wikipedia's list of signs (Kelio ženklai
Lietuvoje), the English page and the drawings of current signs on Wikimedia
Commons.

Sources, in this order (a code on an earlier one keeps that one's image):

- lt:Kelio ženklai Lietuvoje, the signs of annex 1 of the Road Traffic
  Rules (Kelių eismo taisyklės) in nine tables: number, name, image,
  meaning. Images are named after the sign's number: "LT road sign 101.svg",
  "Lithuania road sign 543.svg", with a letter for the drawings of one
  number that differ (604A–604C, 623A–623E), which become codes of their
  own, and an example value for the signs that take any
  ("LT road sign 329 (50).svg", "LT road sign 330-50.svg"). Where Lithuania
  has no drawing of its own the page shows the Russian sign
  ("RU road sign 7.1.svg"); those rows are not read.
- en:Road signs in Lithuania, the same signs in galleries with English
  captions, for 610 (direction for goods vehicles) and 611 (dead end), which
  the Lithuanian page shows only as Russian drawings.
- Commons, "Category:Diagrams of road signs of Lithuania", for the panels
  816 (vehicles with trailers) and 852 (mopeds), which no page shows. Its
  subcategories of historic, Soviet and obsolete drawings and of road number
  plates are not entered, and its drawings 105a (children, on a fluorescent
  board) and 320b (customs, in Lithuanian and English) are not read: the
  rules have no such signs.

The code is taken from the file name (parsers.files()), so captions do not
matter and the Lithuanian names come from translations.csv
(local_names="translations"): the names of the rules as in force in 2026,
which for a few signs differ from the page's (340 is now "Elektrinių
mikrojudumo priemonių eismas draudžiamas", no electric micromobility
vehicles; 846 and 847 say "asmenys su negalia"). Not read, as the rules
repealed them: 630–634 (signs for national and regional parks and
reserves, repealed in 2020), 717 and 721 (2022) and 725 (2023). The
English page's 901–903 (obstacle boards) are not numbered signs of the
rules either. 410 (roundabout) has two drawings on the page, 410a and 410b;
the rules show one, so 410a is read as 410 (corrections.csv) and 410b is
not read.
"""

import os

from ...core import parsers
from ...core.model import Source, commons_category

FILE = (
    r"(?:Lithuania(?:n)? road sign|LT road sign|Kelio ženklas)[ -]?"
    r"(?P<code>\d{3}(?:\.\d+)?[a-zA-Z]?)(?: \([^)]*\)|-\d+)?\.(?:svg|png)"
)

SOURCE = Source(
    country="lt",
    language="lt",
    country_name="Lithuania",
    language_name="Lithuanian",
    wiki="lt.wikipedia.org",
    page=[
        "Kelio ženklai Lietuvoje",
        "en:Road signs in Lithuania",
        commons_category(
            "Diagrams of road signs of Lithuania",
            exclude=r"(?i)historic|obsolete|soviet|route signs|road number|european road|motorway number",
        ),
    ],
    parser=parsers.between(
        parsers.files(FILE, ignore=r" (?:105a|320b|410b|63[0-4]|717|721|725|90[1-3])\.svg$"),
        end=r"^==\s*Historic signs\s*==",
    ),
    local_names="translations",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
