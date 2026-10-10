"""Great Britain: the signs on the English Wikipedia's "Road signs in the United Kingdom".

Images are named after the diagram number in the Traffic Signs Regulations and
General Directions (TSRGD): "UK traffic sign 512 (right).svg". The number,
with its variant, is the code; names come from translations.csv, as the
captions describe the signs rather than name them.

Only the sections about current signs are read: from "Categorisation" up to
"Obsolete", which, with the sections after it (Northern Ireland, Crown
Dependencies, overseas territories), shows older or local versions of the
same signs.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="gb",
    language="en",
    country_name="Great Britain",
    language_name="English",
    wiki="en.wikipedia.org",
    page="Road signs in the United Kingdom",
    parser=parsers.between(
        parsers.files(r"UK traffic sign (?P<code>\d.*)\.svg"),
        start=r"^==\s*Categorisation\s*==",
        end=r"^===\s*Obsolete\s*===",
    ),
    local_names="translations",
    names_key="en-GB",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
