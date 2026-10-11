"""United States: the signs on the English Wikipedia's "Road signs in the United States".

Galleries per MUTCD series (R1 stop and yield, W1 horizontal alignment, …);
see parser.py. The code is the image's name after "MUTCD", the name its
caption.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="us",
    language="en",
    country_name="United States",
    language_name="English",
    wiki="en.wikipedia.org",
    page="Road signs in the United States",
    parser=parse,
    names_key="en-US",
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
