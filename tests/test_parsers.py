import dataclasses
import os
import tempfile
import unittest
from unittest import mock

from pipelines.core import parsers
from pipelines.core.model import Entry, Problem
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
        self.assertIn("Bez kódu.svg", str(problems[0]))


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
        self.assertIn("Bez čísla.svg", str(problems[0]))


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


PL_GALLERY = """<gallery>
Plik:PL road sign A-1.svg|'''A-1'''<br>„niebezpieczny zakręt w prawo”
Plik:PL road sign A-31.svg|'''A-31'''<br />„niebezpieczne pobocze” (wariant){{refn|grupa=uwaga|x}}
Plik:PL road sign F-6a.svg|'''F-6a:''' wariant znaku uprzedzającego
Plik:Sygnalizator SB.svg|'''SB''' „sygnalizator dla autobusów”<ref>Dz.U.</ref>
</gallery>
"""

CZ_TABLE_WITH_NOISE = """{|
|-
| [[Soubor:a.svg]] || IS 3a Směrová tabule s cílem (přímo) 294/2015 Sb.
|-
| [[Soubor:b.svg]] || IS 3a Směrová tabule (s jedním cílem) 30/2001 Sb.
|-
| [[Soubor:c.svg]] || 101 Zámek
|-
| [[Soubor:d.svg]] || V 1a Podélná čára souvislá
|-
| [[Soubor:e.svg]] || odrazky
|}
"""


class CaptionCleanupTest(unittest.TestCase):
    """Markup, quotes, numbering notes and non-sign rows, as on the Polish and Czech pages."""

    def test_br_templates_quotes_and_colon(self):
        parse = parsers.gallery(r"[A-Z]{1,3}(?:-\d+[a-z]?)?", namespaces=("Plik",), strip=r"[„”]")
        entries, problems = parse(PL_GALLERY)
        self.assertEqual(problems, [])
        self.assertEqual(
            [(e.code, e.name) for e in entries],
            [
                ("A-1", "niebezpieczny zakręt w prawo"),
                ("A-31", "niebezpieczne pobocze (wariant)"),
                ("F-6a", "wariant znaku uprzedzającego"),
                ("SB", "sygnalizator dla autobusów"),
            ],
        )

    def test_ignore_patterns_and_strip(self):
        parse = parsers.wikitable(
            r"[A-Z]{1,3} \d+[a-z]?",
            namespaces=("Soubor",),
            ignore=[r"^\d{3} ", r"^V \d", r"30/2001 Sb\.$"],
            strip=r"\s*\d+/\d{4} Sb\.$",
        )
        entries, problems = parse(CZ_TABLE_WITH_NOISE)
        self.assertEqual([(e.code, e.name) for e in entries], [("IS 3a", "Směrová tabule s cílem (přímo)")])
        self.assertEqual([p.file for p in problems], ["e.svg"])


UK_PAGE = """
== History ==
[[File:Pre-Worboys sign.jpg|thumb|An old sign]]
==Warning signs==
<gallery>
File:UK traffic sign 501.svg|[[Stop sign|STOP]] or GIVE WAY ahead
File:UK_traffic_sign_512_(right).svg|Bend to right{{efn|name=left}}
</gallery>
{| class="wikitable"
| [[File:UK traffic sign 601.1.svg|60px]] || Stop
|}
{{Multiple image | image1 = UK traffic sign 616.svg | image2 = UK traffic sign 501.svg}}
"""

DE_GALLERY = """<gallery>
Sinnbild Kfz.svg|Kraftwagen
Zeichen 101 - Gefahrstelle, StVO 1970.svg|'''Zeichen 101'''<br />[[Gefahr]]stelle
Zusatzzeichen 1000-10 - links, StVO 1992.svg|'''Zusatzzeichen 1000-10'''<br />Richtungs&shy;angabe links
RAL-Gütesiegel, 2014.svg|2014 wurde der Block überarbeitet
</gallery>
"""


class FilesTest(unittest.TestCase):
    def test_takes_the_code_from_matching_file_names_anywhere_on_the_page(self):
        entries, problems = parsers.files(r"UK traffic sign (?P<code>.+)\.svg")(UK_PAGE)
        self.assertEqual(problems, [])
        self.assertEqual(
            [(e.file, e.code, e.name) for e in entries],
            [
                ("UK traffic sign 501.svg", "501", ""),
                ("UK traffic sign 512 (right).svg", "512 (right)", ""),
                ("UK traffic sign 601.1.svg", "601.1", ""),
                ("UK traffic sign 616.svg", "616", ""),
            ],
        )

    def test_ignore_and_a_missing_code_group(self):
        parse = parsers.files(r"UK traffic sign (?P<code>.+)\.svg", ignore=r" 6\d\d")
        self.assertEqual([e.code for e in parse(UK_PAGE)[0]], ["501", "512 (right)"])
        with self.assertRaises(ValueError):
            parsers.files(r"UK traffic sign (.+)\.svg")


class CodePrefixTest(unittest.TestCase):
    def test_prefix_is_required_and_left_out_of_the_code(self):
        parse = parsers.gallery(r"\d{3,4}(?:-\d+)*", code_prefix=r"(?:Zusatzzeichen|Zeichen) ", ignore=r"^Kraftwagen$")
        entries, problems = parse(DE_GALLERY)
        self.assertEqual(
            [(e.file, e.code, e.name) for e in entries],
            [
                ("Zeichen 101 - Gefahrstelle, StVO 1970.svg", "101", "Gefahrstelle"),
                ("Zusatzzeichen 1000-10 - links, StVO 1992.svg", "1000-10", "Richtungsangabe links"),
            ],
        )
        self.assertEqual([p.file for p in problems], ["RAL-Gütesiegel, 2014.svg"])  # no "Zeichen": not a code


class SeparatorTest(unittest.TestCase):
    """Captions that put a dot, a dash or a slash after the code, as in France and Canada."""

    def test_dot_dash_slash_and_gallery_options(self):
        page = """<gallery>
Fichier:France road sign A1a.svg|[[Virage|A1a - Virage à droite]]
Signal B0.svg|[[Circulation interdite|B0. Circulation interdite]]
File:CA-ON road sign Ra-009A (B).svg|RA-009A/Cross other side
Zeichen 108-4 - Gefälle.svg|alt=Zeichen 108-4Gefälle 4 %|Zeichen 108-4 Gefälle 4 %
</gallery>"""
        parse = parsers.gallery(r"[A-Z]{1,2}-?\d+[A-Z]?[a-z]?\d?", namespaces=("Fichier",), ignore=r"^Zeichen")
        entries, problems = parse(page)
        self.assertEqual(problems, [])
        self.assertEqual(
            [(e.code, e.name) for e in entries],
            [("A1a", "Virage à droite"), ("B0", "Circulation interdite"), ("RA-009A", "Cross other side")],
        )
        entries, _ = parsers.gallery(r"\d{3}(?:-\d+)?", code_prefix=r"Zeichen ")(page)
        self.assertEqual([(e.code, e.name) for e in entries], [("108-4", "Gefälle 4 %")])  # the alt text is not the caption


class BetweenTest(unittest.TestCase):
    def test_reads_only_from_the_start_heading_to_the_end_heading(self):
        page = UK_PAGE + "===Obsolete===\n<gallery>\nFile:UK traffic sign 504 (1965–1975).svg|Crossroads\n</gallery>\n"
        parse = parsers.between(
            parsers.files(r"UK traffic sign (?P<code>.+)\.svg"), start=r"^==Warning signs==", end=r"^===Obsolete==="
        )
        self.assertEqual([e.code for e in parse(page)[0]], ["501", "512 (right)", "601.1", "616"])
        # Without a start the page is read from the top, without an end to the bottom.
        self.assertEqual(len(parsers.between(parsers.files(r"UK traffic sign (?P<code>.+)\.svg"))(page)[0]), 5)
        self.assertIn("between", parse.label)


class CorrectionsTest(unittest.TestCase):
    def test_a_correction_can_add_a_row_the_parser_could_not_read(self):
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "corrections.csv"), "w", encoding="utf-8") as handle:
                handle.write("file,code,name_sk,note\nC.svg,C-13/16,Droga dla pieszych i rowerów,caption has no code\n")
            source = dataclasses.replace(all_sources()["sk"], data_dir=folder)
            entries = [Entry("A.svg", "A-1", "Zakręt")]
            problems = [Problem("C.svg", "no code"), Problem("X.svg", "no code")]
            changes, left = source.apply_corrections(entries, problems)
        self.assertEqual([(e.file, e.code) for e in entries], [("A.svg", "A-1"), ("C.svg", "C-13/16")])
        self.assertEqual([p.file for p in left], ["X.svg"])
        self.assertEqual(len(changes), 1)


if __name__ == "__main__":
    unittest.main()
