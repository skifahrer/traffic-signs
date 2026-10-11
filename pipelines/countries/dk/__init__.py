"""Denmark: the list of signs on the Danish Wikipedia (Vejtavler i Danmark).

Gallery captions are "A11: Farligt vejkryds, …", code then name. The Danish
list covers the main signs (A–E); the many variants and panels on the
English page have no Danish names there. See parser.py.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="dk",
    language="da",
    country_name="Denmark",
    language_name="Danish",
    wiki="da.wikipedia.org",
    page="Vejtavler i Danmark",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
