"""Countries whose signs are spread over several pages, named in translations.csv, or drawn as PNG."""

import dataclasses
import hashlib
import json
import os
from unittest import mock

from pipelines.core import layout, parsers
from pipelines.core.model import Page, Source
from pipelines.core.sync import Options, sync
from pipelines.core.wikimedia import Client
from tests.support import SK_WIKITEXT, SandboxTestCase

PAGES = {
    ("fr.wikipedia.org", "Panneaux de danger"): "<gallery>\nFichier:France road sign A14.svg|[[Danger|A14 - Danger]]\n</gallery>",
    ("fr.wikipedia.org", "Panneaux de prescription"): "* [[Fichier:France_road_sign_B1.svg|50px]] B1",
    ("en.wikipedia.org", "Road signs in France"): (
        "<gallery>\nFile:France road sign A14.svg|Other danger\nFile:France road sign M9z.svg|Plate\n</gallery>"
    ),
}

TRANSLATIONS = """code,category,slug,name_en,name_fr
A14,warning,danger,Other danger,Autres dangers
B1,regulatory,no-entry,No entry,Sens interdit
M9z,additional-panel,except-cyclists,Except cyclists,Sauf cycles
"""


class MultiPageTest(SandboxTestCase):
    def setUp(self):
        super().setUp()
        data_dir = os.path.join(self.root, "fr")
        os.makedirs(data_dir)
        with open(os.path.join(data_dir, "translations.csv"), "w", encoding="utf-8") as handle:
            handle.write(TRANSLATIONS)
        self.source = Source(
            country="fr",
            language="fr",
            country_name="France",
            language_name="French",
            wiki="fr.wikipedia.org",
            page=["Panneaux de danger", "Panneaux de prescription", "en:Road signs in France"],
            parser=parsers.files(r"(?i:France road sign) (?P<code>[A-Za-z0-9-]+)\.svg"),
            data_dir=data_dir,
            local_names="translations",
        )
        patch = mock.patch.object(Client, "page_wikitext", side_effect=lambda wiki, title: PAGES[(wiki, title)])
        patch.start()
        self.addCleanup(patch.stop)

    def meta(self, category, slug):
        with open(layout.sign_path(category, slug, "fr", "json"), encoding="utf-8") as handle:
            return json.load(handle)

    def test_pages_can_come_from_another_wiki(self):
        self.assertEqual(
            self.source.pages,
            (
                Page("fr.wikipedia.org", "Panneaux de danger"),
                Page("fr.wikipedia.org", "Panneaux de prescription"),
                Page("en.wikipedia.org", "Road signs in France"),
            ),
        )
        self.assertEqual(self.source.page_url, "https://fr.wikipedia.org/wiki/Panneaux_de_danger")

    def test_reads_every_page_and_takes_names_from_translations(self):
        result = sync(self.source, Client(delay=0), Options(no_images=True))
        self.assertEqual(result.errors, [])
        self.assertEqual((result.entries, result.synced, result.renamed), (3, 3, []))
        self.assertEqual(layout.read_translations("warning", "danger"), {"en": "Other danger", "fr": "Autres dangers"})
        self.assertEqual(layout.read_translations("regulatory", "no-entry"), {"en": "No entry", "fr": "Sens interdit"})
        # Each sign remembers the page it was found on first.
        self.assertEqual(self.meta("warning", "danger")["source"]["page"], "https://fr.wikipedia.org/wiki/Panneaux_de_danger")
        self.assertEqual(
            self.meta("additional-panel", "except-cyclists")["source"]["page"],
            "https://en.wikipedia.org/wiki/Road_signs_in_France",
        )

    def test_a_code_found_on_an_earlier_page_wins(self):
        pages = dict(PAGES)
        pages[("en.wikipedia.org", "Road signs in France")] = "<gallery>\nFile:France road sign A14 (old).svg|x\n</gallery>"
        parser = parsers.files(r"(?i:France road sign) (?P<code>[A-Za-z0-9-]+)(?: \(old\))?\.svg")
        with mock.patch.object(Client, "page_wikitext", side_effect=lambda wiki, title: pages[(wiki, title)]):
            result = sync(dataclasses.replace(self.source, parser=parser), Client(delay=0), Options(no_images=True))
        self.assertEqual(result.errors, [])
        self.assertEqual(result.entries, 2)
        self.assertEqual(self.meta("warning", "danger")["source"]["file"], "France road sign A14.svg")

    def test_local_names_must_be_page_or_translations(self):
        with self.assertRaises(ValueError):
            dataclasses.replace(self.source, local_names="csv")


class PreferSvgTest(SandboxTestCase):
    """A page showing a PNG gets the SVG of the same name when Commons has one."""

    wikitext = SK_WIKITEXT.replace("101 Nebezpečenstvo.svg", "101 Nebezpečenstvo.png")
    PNG, SVG = b"\x89PNG old", b"<svg xmlns='http://www.w3.org/2000/svg'/>"

    def setUp(self):
        super().setUp()
        self.commons = {
            "File:101 Nebezpečenstvo.png": self.PNG,
            "File:110-10 Zákruta (vľavo).svg": self.SVG,
            "File:240-8,5 Maximálna hmotnosť (8,5 t).svg": self.SVG,
        }
        for patch in (
            mock.patch.object(Client, "image_info", side_effect=self.image_info),
            mock.patch.object(Client, "get", side_effect=lambda url: self.commons[url.split("/", 3)[3]]),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def image_info(self, api, titles):
        return {
            t: {
                "title": t,
                "url": "https://upload.wikimedia.org/" + t,
                "description_url": "https://commons.wikimedia.org/wiki/" + t,
                "sha1": hashlib.sha1(self.commons[t]).hexdigest(),
                "mime": None,
                "license": "Public domain",
                "license_url": None,
                "author": "MDV SR",
            }
            for t in titles
            if t in self.commons and "commons" in api
        }

    def danger_files(self):
        return sorted(os.listdir(self.path("warning", "danger", "sk")))

    def test_keeps_the_png_when_there_is_no_svg(self):
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(self.danger_files(), ["danger-sk.json", "danger-sk.png"])

    def test_switches_to_the_svg_and_drops_the_png(self):
        self.run_pipeline()
        self.commons["File:101 Nebezpečenstvo.svg"] = self.SVG
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(self.danger_files(), ["danger-sk.json", "danger-sk.svg"])
        with open(self.path("warning", "danger", "sk", "danger-sk.json"), encoding="utf-8") as handle:
            meta = json.load(handle)
        self.assertEqual(meta["image"]["file"], "danger-sk.svg")
        self.assertEqual(meta["source"]["file"], "101 Nebezpečenstvo.svg")


class EnglishSpeakingCountryTest(SandboxTestCase):
    """Great Britain: the shared English name, and its own wording under en-GB."""

    def setUp(self):
        super().setUp()
        data_dir = os.path.join(self.root, "gb")
        os.makedirs(data_dir)
        with open(os.path.join(data_dir, "translations.csv"), "w", encoding="utf-8") as handle:
            handle.write("code,category,slug,name_en,name_en-GB\n602,regulatory,give-way,Give way,Give way to traffic on the major road\n")
        self.source = Source(
            country="gb",
            language="en",
            country_name="Great Britain",
            language_name="English",
            wiki="en.wikipedia.org",
            page="Road signs in the United Kingdom",
            parser=parsers.files(r"UK traffic sign (?P<code>\d.*)\.svg"),
            data_dir=data_dir,
            local_names="translations",
            names_key="en-GB",
        )
        patch = mock.patch.object(Client, "page_wikitext", return_value="[[File:UK traffic sign 602.svg|60px]]")
        patch.start()
        self.addCleanup(patch.stop)

    def test_writes_the_shared_name_and_the_local_one_next_to_it(self):
        self.assertEqual((self.source.name_key, self.source.local_name_column), ("en-GB", "name_en-GB"))
        result = sync(self.source, Client(delay=0), Options(no_images=True))
        self.assertEqual((result.errors, result.synced), ([], 1))
        self.assertEqual(
            layout.read_translations("regulatory", "give-way"),
            {"en": "Give way", "en-GB": "Give way to traffic on the major road"},
        )
