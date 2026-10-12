"""Netherlands: the Dutch and the English Wikipedia lists of signs.

Sources:

- nl:Verkeersborden in Nederland, the series A–L of the RVV 1990, with
  captions "A1: Maximumsnelheid (1)": code, name and the number the sign had
  in the RVV 1966 in brackets.
- en:Road signs in the Netherlands, the same series with English captions
  ("A1: Speed limit (50 km/h)"), plus K5, K6, K12, K13 and K14, signs from
  the road-marking (BB01 exit, BB13 narrowing marker, BB23-1 to -3 level
  crossing countdown markers) and signposting (BW501, BW501e: U-route
  diversion) catalogues, L51 (fietsstraat), L401 (national speed limits at
  the border, the page's lead image), L403 (EU country border) and C2f with
  panel OB705 ("ga terug", against wrong-way drivers).

The Dutch page comes first. A sign on both pages counts once, under the
Dutch page's image: the English page draws E6 (with panel BT17), E13, G13,
G14, H1, H2, K3, L13 and L16 from other files, and the sync keeps the first
page's entry for a code. Because the English captions are English, the
Dutch names come from the name_nl column of translations.csv
(local_names="translations"): for the RVV 1990 signs that column holds the
Dutch page's captions, for the others the wording of the RVV/BABW or the
Commons file description.

Not read (see parser.py for how):

- Dutch page, after "Contrasterende bies": the same signs with and without a
  white border, temporary detour signs, Frisian signs, toll, fatbike and zone
  signs, and the environmental-zone signs C22a–C22d with their panels,
  replaced by C22e in 2025.
- English page: the temporary diversion signs "Omleiding 1–3" and the
  motorway diversion announcement, which have no code; the bilingual
  Dutch-Frisian versions of G13, C2f + OB705, BB01, OB54 and a place-name
  sign (H01d), which are regional; the e-TOL signs of the A24 and the
  Vondelpark fatbike ban, which have no code (the latter is local); the
  examples of direction signs outside the galleries (K4 after the
  Rijkswaterstaat guidelines, K6–K8 after the Richtlijn Bewegwijzering 2025);
  photos; and every retired sign: the 1935–1951, 1951–1966 and 1966–1990
  series and C22a/C22b.
"""

import os

from ...core.model import Source
from .parser import parse

SOURCE = Source(
    country="nl",
    language="nl",
    country_name="Netherlands",
    language_name="Dutch",
    wiki="nl.wikipedia.org",
    page=["Verkeersborden in Nederland", "en:Road signs in the Netherlands"],
    parser=parse,
    data_dir=os.path.dirname(os.path.abspath(__file__)),
    local_names="translations",
)
