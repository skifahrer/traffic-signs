import dataclasses
import unittest
from unittest import mock

from pipelines.core import parsers
from pipelines.core.model import Entry
from pipelines.countries import all_sources
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

SK_GALLERY = parsers.gallery(r"\d{3}(?:-[0-9]+(?:,[0-9]+)?)*", namespaces=("Súbor",))
CZ_TABLE = parsers.wikitable(r"[A-Z]{1,2} \d+[a-z]?", namespaces=("Soubor",))


class GalleryTest(unittest.TestCase):
    def test_reads_captions_inside_galleries_only(self):
        entries, problems = SK_GALLERY(SK_WIKITEXT + "<gallery>\nSúbor:Bez kódu.svg|Značka bez kódu\n</gallery>\n")
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
        entries, problems = CZ_TABLE(TABLE)
        self.assertEqual(
            [(e.file, e.code, e.name) for e in entries],
            [
                ("Czech Republic road sign A 1a.svg", "A 1a", "Zatáčka vpravo"),
                ("Czech Republic road sign IP 4b.svg", "IP 4b", "Jednosměrný provoz"),
            ],
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("Bez čísla.svg", problems[0])


class SeveralParsersTest(unittest.TestCase):
    """A country can list several parsers, including functions of its own."""

    def source(self, *chosen):
        return dataclasses.replace(all_sources()["sk"], parser=list(chosen))

    def parse(self, source, wikitext):
        with mock.patch("builtins.print"):
            return source.parse(wikitext)

    def test_combines_a_gallery_and_a_table_on_one_page(self):
        entries, problems = self.parse(self.source(SK_GALLERY, CZ_TABLE), SK_WIKITEXT + TABLE)
        self.assertEqual([e.code for e in entries], ["101", "110-10", "240-5,5", "A 1a", "IP 4b"])
        self.assertEqual(len(problems), 1)  # the table row without a number

    def test_a_row_read_by_two_parsers_counts_once(self):
        entries, _ = self.parse(self.source(SK_GALLERY, SK_GALLERY), SK_WIKITEXT)
        self.assertEqual(len(entries), 3)

    def test_a_country_can_bring_its_own_parser(self):
        def bullet_list(wikitext):
            return [Entry("Sign 7.svg", "7", "Seven")], []

        entries, problems = self.parse(self.source(SK_GALLERY, bullet_list), SK_WIKITEXT)
        self.assertEqual([e.code for e in entries], ["101", "110-10", "240-5,5", "7"])
        self.assertEqual(problems, [])

    def test_a_single_parser_needs_no_list(self):
        source = dataclasses.replace(all_sources()["sk"], parser=SK_GALLERY)
        self.assertEqual(source.parsers, (SK_GALLERY,))


if __name__ == "__main__":
    unittest.main()
