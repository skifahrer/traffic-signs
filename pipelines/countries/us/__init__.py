"""United States: the signs on the English Wikipedia's "Road signs in the United States".

Gallery lines look like `File:MUTCD R1-1.svg|R1-1<br>Stop`, one gallery per
MUTCD series. Variants of a sign (a fluorescent or yellow version, with or
without a legend) share the code in their captions, so the code is taken
from the image name instead ("R1-6 (yellow)"), and the name from the caption
after the code. A drawing marked "(old)" is the previous version of a sign
shown next to the current one and is skipped.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="us",
    language="en",
    country_name="United States",
    language_name="English",
    wiki="en.wikipedia.org",
    page="Road signs in the United States",
    parser=parsers.named_files(
        r"MUTCD (?P<code>[A-Z]+\d.*)\.svg",
        caption_code=r"[A-Z]+\d[\w.()-]*\s+",
        ignore=r"\(old\)\.svg$",
    ),
    names_key="en-US",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
