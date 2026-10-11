"""Greece: the list of signs on the Greek Wikipedia (Κώδικας Οδικής Κυκλοφορίας, ΚΟΚ 2009).

Gallery lines look like `Αρχείο:Traffic Sign GR - KOK 2009 - Κ-1α.svg|'''Κ-1α''' Επικίνδυνη στροφή (αριστερή)`;
codes are a series in Greek letters (Κ warning, Ρ regulatory, Π information,
Πρ additional panels), a number and an optional Greek letter: Κ-1α, Ρ-33, Πρ-4.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="gr",
    language="el",
    country_name="Greece",
    language_name="Greek",
    wiki="el.wikipedia.org",
    page="Πινακίδες οδοσήμανσης στην Ελλάδα",
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
)
