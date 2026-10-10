"""Canada: the national signs on the English Wikipedia's "Road signs in Canada".

Signs are set by each province; the page shows the national examples from the
Manual of Uniform Traffic Control Devices for Canada (MUTCDC) first, under
"Canadian road signs", then each province's own. Only the national section is
read. Gallery captions start with the MUTCDC code: `RA-2<br/>Yield`.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="ca",
    language="en",
    country_name="Canada",
    language_name="English",
    wiki="en.wikipedia.org",
    page="Road signs in Canada",
    parser=parsers.between(
        parsers.gallery(
            r"[A-Z]{2}-\d+[A-Z]*",
            ignore=r"^Stop \((?!English\))",  # the stop sign in French and other languages
        ),
        start=r"^==\s*Canadian road signs\s*==",
        end=r"^==[^=]",
    ),
    names_key="en-CA",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
