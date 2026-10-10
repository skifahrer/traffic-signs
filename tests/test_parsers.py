import unittest

from pipelines.core import parsers
from tests.support import SK_WIKITEXT

TABLE = """
{| class="wikitable"
! Vyobrazení !! Číslo a název !! Význam
|-
|align="center"|[[Soubor:Czech Republic road sign A 1a.svg|120px]]
| A 1a '''[[Zatáčka]] vpravo'''
| Upozorňuje na směrový oblouk.
|-
| [[Soubor:Czech Republic road sign IP 4b.svg|120px]] || IP 4b '''Jednosměrný provoz''' || ...
|-
|align="center"|[[Soubor:Bez čísla.svg|120px]]
| Bez čísla
|}
"""


class GalleryTest(unittest.TestCase):
    def test_reads_captions_inside_galleries_only(self):
        parse = parsers.gallery(r"\d{3}(?:-[0-9]+(?:,[0-9]+)?)*", namespaces=("Súbor",))
        entries, problems = parse(SK_WIKITEXT + "<gallery>\nSúbor:Bez kódu.svg|Značka bez kódu\n</gallery>\n")
        self.assertEqual(
            [(e.file, e.code, e.name) for e in entries],
            [
                ("101 Nebezpečenstvo.svg", "101", "Nebezpečenstvo"),
                ("110-10 Zákruta (vľavo).svg", "110-10", "Zákruta (vľavo)"),
                ("240-8,5 Maximálna hmotnosť (8,5 t).svg", "240-5,5", "Maximálna hmotnosť (8,5 t)"),
            ],
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("Bez kódu.svg", problems[0])


class WikitableTest(unittest.TestCase):
    def test_reads_image_and_the_code_cell_after_it(self):
        parse = parsers.wikitable(r"[A-Z]{1,2} \d+[a-z]?", namespaces=("Soubor",))
        entries, problems = parse(TABLE)
        self.assertEqual(
            [(e.file, e.code, e.name) for e in entries],
            [
                ("Czech Republic road sign A 1a.svg", "A 1a", "Zatáčka vpravo"),
                ("Czech Republic road sign IP 4b.svg", "IP 4b", "Jednosměrný provoz"),
            ],
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("Bez čísla.svg", problems[0])


if __name__ == "__main__":
    unittest.main()
