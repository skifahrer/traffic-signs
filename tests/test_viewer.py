import json
import os

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

    def test_a_country_without_a_pipeline_still_shows(self):
        os.makedirs(self.path("warning", "danger", "at"))
        layout.write_json(
            layout.sign_path("warning", "danger", "at", "json"),
            {"sign": "danger", "category": "warning", "country": "at", "code": "A 1"},
        )
        index = build_index()
        self.assertEqual(index["countries"]["at"]["name"], "AT")
        self.assertEqual(sorted(self.sign(index, "danger")["countries"]), ["at", "sk"])

    def test_build_writes_the_site(self):
        out = os.path.join(self.root, "_site")
        build(out)
        for name in ("index.html", "app.js", "style.css", "data.json"):
            self.assertTrue(os.path.exists(os.path.join(out, name)), name)
        self.assertTrue(os.path.exists(os.path.join(out, "signs", "warning", "danger", "danger.json")))
        with open(os.path.join(out, "data.json"), encoding="utf-8") as handle:
            self.assertEqual(len(json.load(handle)["signs"]), 3)
