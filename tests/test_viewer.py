import json
import os
import re

from pipelines.core import layout
from tests.support import SandboxTestCase
from viewer.__main__ import build
from viewer.index import build_index


class ViewerTest(SandboxTestCase):
    def setUp(self):
        super().setUp()
        self.run_pipeline("--no-images")

    def sign(self, index, slug):
        return next(s for s in index["signs"] if s["sign"] == slug)

    def test_index_lists_every_sign_with_names_and_countries(self):
        index = build_index()
        self.assertEqual(index["countries"]["sk"], {"name": "Slovakia", "language": "sk", "language_name": "Slovak"})
        self.assertEqual(list(index["categories"]), list(layout.CATEGORIES))
        self.assertEqual(
            {f"{s['category']}/{s['sign']}" for s in index["signs"]},
            {"warning/danger", "warning/bend-left", "regulatory/maximum-weight-8-5t"},
        )
        bend = self.sign(index, "bend-left")
        self.assertEqual(bend["names"], {"en": "Bend (left)", "sk": "Zákruta (vľavo)"})
        self.assertEqual(bend["countries"]["sk"]["code"], "110-10")
        self.assertIsNone(bend["countries"]["sk"]["image"])  # synced without images

    def test_image_paths_and_archive_are_relative_to_the_site(self):
        meta_path = layout.sign_path("warning", "danger", "sk", "json")
        with open(meta_path, encoding="utf-8") as handle:
            meta = json.load(handle)
        meta["image"] = {"file": "danger-sk.svg", "license": "Public domain", "author": "MDV SR", "source": "https://x"}
        meta["archived"] = [{"file": "danger-sk-archived-2020.svg", "valid_until": 2020}]
        meta["valid_until"] = 2026
        layout.write_json(meta_path, meta)

        entry = self.sign(build_index(), "danger")["countries"]["sk"]
        self.assertEqual(entry["image"], "signs/warning/danger/sk/danger-sk.svg")
        self.assertEqual(entry["license"], "Public domain")
        self.assertEqual(entry["valid_until"], 2026)
        self.assertEqual(entry["archived"], [{"image": "signs/warning/danger/sk/danger-sk-archived-2020.svg", "valid_until": 2020}])

    def test_tiff_images_are_shown_through_the_wiki_thumbnail(self):
        meta_path = layout.sign_path("warning", "danger", "sk", "json")
        with open(meta_path, encoding="utf-8") as handle:
            meta = json.load(handle)
        meta["image"] = {
            "file": "danger-sk.tif",
            "source": "https://commons.wikimedia.org/wiki/File:IS_12d_N%C3%A1hradn%C3%AD_trasa.tif",
        }
        layout.write_json(meta_path, meta)

        entry = self.sign(build_index(), "danger")["countries"]["sk"]
        self.assertEqual(
            entry["image"],
            "https://commons.wikimedia.org/wiki/Special:FilePath/IS_12d_N%C3%A1hradn%C3%AD_trasa.tif?width=320",
        )

    def test_a_country_without_a_pipeline_still_shows(self):
        os.makedirs(self.path("warning", "danger", "xx"))
        layout.write_json(
            layout.sign_path("warning", "danger", "xx", "json"),
            {"sign": "danger", "category": "warning", "country": "xx", "code": "A 1"},
        )
        index = build_index()
        self.assertEqual(index["countries"]["xx"]["name"], "XX")
        self.assertEqual(sorted(self.sign(index, "danger")["countries"]), ["sk", "xx"])

    def test_build_writes_the_site(self):
        out = os.path.join(self.root, "_site")
        build(out)
        for name in ("index.html", "app.js", "style.css", "data.json"):
            self.assertTrue(os.path.exists(os.path.join(out, name)), name)
        self.assertTrue(os.path.exists(os.path.join(out, "signs", "warning", "danger", "danger.json")))
        with open(os.path.join(out, "data.json"), encoding="utf-8") as handle:
            self.assertEqual(len(json.load(handle)["signs"]), 3)
        # Every build asks for its own files, so a cached app.js never reads an older data.json.
        with open(os.path.join(out, "index.html"), encoding="utf-8") as handle:
            html = handle.read()
        with open(os.path.join(out, "app.js"), encoding="utf-8") as handle:
            app = handle.read()
        self.assertRegex(html, r'src="app\.js\?v=[0-9a-f]{10}"')
        self.assertRegex(html, r'href="style\.css\?v=[0-9a-f]{10}"')
        self.assertRegex(app, r'fetch\("data\.json\?v=[0-9a-f]{10}"\)')
        # The preload asks for the same URL as app.js, so data.json downloads once, early.
        version = re.search(r'data\.json\?v=([0-9a-f]{10})', app).group(1)
        self.assertIn(f'<link rel="preload" href="data.json?v={version}" as="fetch" crossorigin="anonymous" />', html)


class VariantTest(SandboxTestCase):
    def test_a_variant_is_the_parent_name_plus_a_side_value_or_letter(self):
        from viewer.index import variant_parent

        signs = {"crosswind", "speed-limit", "no-parking", "level-crossing-countdown-marker-3-bars", "steep-descent", "farm-animals"}
        for slug, parent in [
            ("crosswind-from-left", "crosswind"),
            ("speed-limit-50", "speed-limit"),
            ("speed-limit-20mph", "speed-limit"),
            ("steep-descent-10-percent", "steep-descent"),
            ("farm-animals-b", "farm-animals"),
            ("level-crossing-countdown-marker-3-bars-left-side", "level-crossing-countdown-marker-3-bars"),
            ("level-crossing-countdown-marker-3-bars-with-distance-left-side", None),  # another sign, with a side
            ("no-parking-zone", None),  # another sign
            ("crosswind", None),
        ]:
            with self.subTest(slug=slug):
                self.assertEqual(variant_parent(slug, signs), parent)

    def test_index_links_variants_to_their_sign(self):
        self.run_pipeline("--no-images")
        names = {"en": "Bend"}
        layout.write_json(layout.translations_path("warning", "bend"), names)
        layout.write_json(layout.sign_path("warning", "bend", "cz", "json"), {"code": "A 1"})
        index = build_index()
        bend = next(s for s in index["signs"] if s["sign"] == "bend")
        left = next(s for s in index["signs"] if s["sign"] == "bend-left")
        self.assertEqual(bend["variants"], ["bend-left"])
        self.assertEqual(left["variant_of"], "bend")
        self.assertNotIn("variant_of", bend)


class SharePagesTest(SandboxTestCase):
    def test_a_page_per_sign_and_category_with_preview_tags(self):
        self.run_pipeline("--no-images")
        meta_path = layout.sign_path("warning", "danger", "sk", "json")
        with open(meta_path, encoding="utf-8") as handle:
            meta = json.load(handle)
        meta["image"] = {"file": "danger-sk.svg", "source": "https://commons.wikimedia.org/wiki/File:101_Nebezpe%C4%8Denstvo.svg"}
        layout.write_json(meta_path, meta)
        out = os.path.join(self.root, "_site")
        build(out, "https://example.org/signs")

        with open(os.path.join(out, "share", "warning", "danger", "index.html"), encoding="utf-8") as handle:
            page = handle.read()
        self.assertIn('<meta property="og:title" content="Other danger – Traffic signs" />', page)
        self.assertIn('content="https://example.org/signs/share/warning/danger/"', page)
        self.assertIn("Slovakia 101", page)
        # A PNG that Commons renders from the SVG, linked directly.
        self.assertRegex(page, r'og:image" content="https://upload\.wikimedia\.org/wikipedia/commons/thumb/\w/\w\w/101_Nebezpe%C4%8Denstvo\.svg/500px-101_Nebezpe%C4%8Denstvo\.svg\.png"')
        self.assertIn('url=../../../#warning/danger"', page)

        with open(os.path.join(out, "share", "warning", "index.html"), encoding="utf-8") as handle:
            category = handle.read()
        self.assertIn("Warning signs – Traffic signs", category)
        self.assertIn('url=../../?type=warning"', category)
        # A sign without an image on Commons has a preview without a picture.
        with open(os.path.join(out, "share", "warning", "bend-left", "index.html"), encoding="utf-8") as handle:
            self.assertNotIn("og:image", handle.read())


class GroupTest(SandboxTestCase):
    def test_every_country_with_a_pipeline_is_on_a_continent(self):
        from pipelines.countries import all_sources
        from viewer.groups import CONTINENT, GROUPS, REGION

        on_a_continent = {c for g in GROUPS if g["kind"] == CONTINENT for c in g["members"]}
        in_a_region_group = {c for g in GROUPS if g["kind"] == REGION for c in g["members"]}
        for country in all_sources():
            with self.subTest(country=country):
                if "-" in country:  # a region: its country is on a continent, and it is in a region group
                    self.assertIn(country.split("-")[0], on_a_continent)
                    self.assertIn(country, in_a_region_group, "add it to its group of regions in viewer/groups.py")
                else:
                    self.assertIn(country, on_a_continent, "add it to its continent in viewer/groups.py")
        for group in GROUPS:
            with self.subTest(group=group["id"]):
                code = r"[a-z]{2}-[a-z0-9]{1,3}" if group["kind"] == REGION else r"[a-z]{2}"
                self.assertTrue(all(re.fullmatch(code, c) for c in group["members"]), group["members"])
        sizes = {g["id"]: len(g["members"]) for g in GROUPS}
        self.assertEqual((sizes["eu"], sizes["eu-us"], sizes["nato"], sizes["five-eyes"], sizes["g7"]), (27, 28, 32, 5, 7))

    def test_data_lists_each_group_with_the_countries_that_have_signs(self):
        self.run_pipeline("--no-images")
        groups = {g["id"]: g for g in build_index()["groups"]}
        self.assertEqual(groups["eu"]["countries"], ["sk"])
        self.assertEqual(groups["eu"]["members"], 27)
        self.assertEqual(groups["visegrad"]["countries"], ["sk"])
        self.assertEqual(groups["mercosur"]["countries"], [])  # listed, but cannot be chosen yet
        self.assertEqual(groups["europe"]["kind"], "continent")
