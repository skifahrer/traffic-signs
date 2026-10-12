"""Ireland: the signs on the English Wikipedia's "Road signs in Ireland".

Gallery captions start with the code from the Traffic Signs Manual (TSM) and
the Road Traffic (Signs) Regulations, in bold, followed by the name:
`'''RUS 001'''<br>Keep Left`, `'''W 002L'''<br>Side Road - Left`. Codes
have a series prefix (F information, RUS regulatory, W warning, WK
roadworks, P supplementary plates, C cycle, RTS/RPC/S traffic signals) and a
three-digit number with an optional suffix. One caption starts with "Sign"
(`Sign F 221L`), which is not part of the code.

The directional and other information signs at the top of the page (map
type, stack type, gantry, town, county boundary, toll and Gaeltacht signs)
are example layouts without a code and are skipped. Variants that share a
code on the page (the Irish versions of Yield and Go, the round bus stop
sign, the diverted traffic arrows and the traffic signal heads) get a code
of their own in corrections.csv, as do a few captions whose code does not
match the image. Names on the page are the Irish (English-language) names,
kept as `en-IE`.
"""

import os

from ...core import parsers
from ...core.model import Source

CODE = r"(?:RUS|RTS|RPC|WK|[CFPSW]) \d{3}(?:\.\d)?[A-Za-z]{0,2}"

SOURCE = Source(
    country="ie",
    language="en",
    country_name="Ireland",
    language_name="English",
    wiki="en.wikipedia.org",
    page="Road signs in Ireland",
    parser=parsers.gallery(
        CODE,
        code_prefix=r"(?:Sign )?",
        ignore=rf"^(?!(?:Sign )?{CODE}\s)",  # example layouts without a code
    ),
    names_key="en-IE",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
