"""US states (and DC, Puerto Rico): each state's own signs, starting with its state route shield.

Run together as `python -m pipelines us-states`. Each state is a region with
its ISO 3166-2 code ("us-ca") and a folder here ("ca/") with its
translations.csv, so state-specific signs can be added one state at a time.

The shield is read from the state's Wikipedia road data module (see
parser.py), the source Wikipedia's own route markers come from, so a state
that redesigns its shield is followed. ROUTES picks the route whose shield
is shown when route 1 has none, or a special design.
"""

import os

from ...core.model import Source
from .parser import shield_parser

# ISO 3166-2 subdivision code: name
STATES = {
    "al": "Alabama", "ak": "Alaska", "az": "Arizona", "ar": "Arkansas", "ca": "California",
    "co": "Colorado", "ct": "Connecticut", "de": "Delaware", "dc": "District of Columbia",
    "fl": "Florida", "ga": "Georgia", "hi": "Hawaii", "id": "Idaho", "il": "Illinois",
    "in": "Indiana", "ia": "Iowa", "ks": "Kansas", "ky": "Kentucky", "la": "Louisiana",
    "me": "Maine", "md": "Maryland", "ma": "Massachusetts", "mi": "Michigan", "mn": "Minnesota",
    "ms": "Mississippi", "mo": "Missouri", "mt": "Montana", "ne": "Nebraska", "nv": "Nevada",
    "nh": "New Hampshire", "nj": "New Jersey", "nm": "New Mexico", "ny": "New York",
    "nc": "North Carolina", "nd": "North Dakota", "oh": "Ohio", "ok": "Oklahoma", "or": "Oregon",
    "pa": "Pennsylvania", "pr": "Puerto Rico", "ri": "Rhode Island", "sc": "South Carolina",
    "sd": "South Dakota", "tn": "Tennessee", "tx": "Texas", "ut": "Utah", "vt": "Vermont",
    "va": "Virginia", "wa": "Washington", "wv": "West Virginia", "wi": "Wisconsin", "wy": "Wyoming",
}  # fmt: skip

# The route whose shield stands for the state, where there is no state route 1
# (route 1 is a US route there, or the numbers start higher).
ROUTES = {
    "az": "87", "ct": "2", "dc": "295", "fl": "60", "hi": "11", "ks": "10", "me": "3", "md": "2",
    "ma": "2", "ne": "2", "nv": "28", "nh": "9", "nj": "3", "ny": "2", "nc": "12", "oh": "2",
    "or": "8", "pa": "3", "ri": "2", "sc": "2", "sd": "10", "tx": "6", "ut": "9", "vt": "100",
    "va": "7", "wa": "9", "wv": "2", "wi": "13", "wy": "22",
}  # fmt: skip

HERE = os.path.dirname(os.path.abspath(__file__))

SOURCES = [
    Source(
        country=f"us-{code}",
        language="en",
        country_name=name,
        language_name="English",
        wiki="en.wikipedia.org",
        page=f"Module:Road data/strings/USA/{code.upper()}",
        parser=shield_parser(code.upper(), ROUTES.get(code, "1")),
        data_dir=os.path.join(HERE, code),
        names_key=f"en-US-{code.upper()}",
        bundle="us-states",
    )
    for code, name in STATES.items()
]
