"""Australia: the national signs on the English Wikipedia's "Road signs in Australia".

Gallery lines look like `File:Australia road sign R1-1.svg|(R1-1) Stop`
(Australian Standard AS 1742 codes). Only the national drawings
("Australia road sign …") of current signs are read: from "Regulatory signs"
up to "Combo signs". Signs only used in one state ("(used in Victoria)"),
signs combined with a plate ("R4-1 (40) + R4-3") and the later sections
(route shields, traffic lights, retired signs) are left out. The code is the
image's name after "Australia road sign", as variants share the code in
their captions.
"""

import os

from ...core import parsers
from ...core.model import Source

SOURCE = Source(
    country="au",
    language="en",
    country_name="Australia",
    language_name="English",
    wiki="en.wikipedia.org",
    page="Road signs in Australia",
    parser=parsers.between(
        parsers.named_files(
            r"Australia road sign (?P<code>[A-Z]+\d[^+]*)\.svg",
            caption_code=r"\([^)]*\)\s*",
            ignore=[r"\(used in ", r"\(used only in ", r"\+"],
            strip=r"\s*\((?:optional|alternative)[^)]*\)$",
        ),
        start=r"^==\s*Regulatory signs\s*==",
        end=r"^==\s*Combo signs\s*==",
    ),
    names_key="en-AU",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
