"""Croatia: the Croatian Wikipedia's list of signs (Dodatak:Prometni znakovi u
Hrvatskoj) and the drawings of current signs on Wikimedia Commons.

Sources, in this order (a code on an earlier one keeps that one's image):

- hr:Dodatak:Prometni znakovi u Hrvatskoj, the signs of the Pravilnik o
  prometnim znakovima, signalizaciji i opremi na cestama (NN 92/2019) in six
  galleries (A danger, B regulatory, C information, D direction, E additional
  panels). Captions are "'''A01'''<br>Opasnost na cesti": the code in bold,
  then the name. The code is taken from the caption, not from the file name:
  the page shows several drawings named after the 2005 numbering
  ("Prometni znak C79.svg" is sign C76, "Croatia road sign E23.svg" is E10).
- Commons, "Category:Diagrams of road signs of Croatia", for C18-1, C79-1 to
  C79-3 and E04-1, which the page lacks. Only the drawings named after the
  current numbering are read ("HR road sign C79-1.svg"); "Prometni znak …",
  "Croatia road sign …" and "Croatian road sign …" drawings follow the 2005
  numbering, and their numbers would land on the wrong signs. Drawings with a
  value in the name ("HR road sign B30 (30).svg") and combinations
  ("HR road sign B01+HR road sign E01.svg") are left out too. The
  subcategories of historic signs (including the 2005 set and the historic
  additional panels), Yugoslav signs, road and route numbers, motorway exit
  signs and road markings are not entered.

en:Road signs in Croatia shows the same signs with English captions and adds
none, so it is not read.

Codes have two digits after the letter, as on the page and in the
regulations (A04, not A4); parser.py makes the codes read from file names
follow that form. The Croatian names come from translations.csv
(local_names="translations"): for the signs on the page they are its
captions, with spelling fixed and a short note in brackets where several
signs share one caption (the direction of a mandatory arrow, the side of a
countdown marker); the page swaps the captions of A09-1 (dip) and A09-2
(bumps and dips), and translations.csv follows the regulations.
"""

import os

from ...core import parsers
from ...core.model import Source, commons_category
from .parser import padded

CODE = r"[A-K]\d{2,3}(?:-\d+)?"

SOURCE = Source(
    country="hr",
    language="hr",
    country_name="Croatia",
    language_name="Croatian",
    wiki="hr.wikipedia.org",
    page=[
        "Dodatak:Prometni znakovi u Hrvatskoj",
        commons_category(
            "Diagrams of road signs of Croatia",
            exclude=r"(?i)historic|yugoslavia|european road|road number|motorway exit|road markings|paris convention",
        ),
    ],
    parser=[
        padded(parsers.gallery(CODE, namespaces=("Datoteka",))),
        padded(parsers.files(rf"HR road sign (?P<code>{CODE})\.svg")),
    ],
    local_names="translations",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
