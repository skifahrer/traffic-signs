import hashlib
import json
import os
from unittest import mock

from pipelines.core import layout
from pipelines.core.wikimedia import Client
from tests.support import SK_SIGNS, SK_WIKITEXT, SandboxTestCase


class SyncTest(SandboxTestCase):
    def test_writes_names_and_metadata_and_is_idempotent(self):
        self.assertEqual(self.run_pipeline("--no-images"), 0)
        self.assertEqual(os.listdir(self.path("warning", "bend-left", "sk")), ["bend-left-sk.json"])
        self.assertEqual(layout.read_translations("warning", "bend-left"), {"en": "Bend (left)", "sk": "Zákruta (vľavo)"})
        # corrections.csv turned the page's wrong code 240-5,5 into 240-8,5
        with open(self.path("regulatory", "maximum-weight-8-5t", "sk", "maximum-weight-8-5t-sk.json")) as handle:
            self.assertEqual(json.load(handle)["code"], "240-8,5")
        self.assertEqual(set(layout.existing_signs("sk", "sk-wikipedia")), SK_SIGNS)

        before = self.snapshot()
        self.assertEqual(self.run_pipeline("--no-images"), 0)
        self.assertEqual(self.snapshot(), before)

    def test_check_writes_nothing(self):
        self.assertEqual(self.run_pipeline("--no-images", "--check"), 0)
        self.assertFalse(os.path.exists(self.path()))

    def test_keeps_other_languages_in_the_names_file(self):
        layout.update_translations("warning", "bend-left", {"cs": "Zatáčka vlevo", "en": "Old English name"})
        self.assertEqual(self.run_pipeline("--no-images"), 0)
        with open(self.path("warning", "bend-left", "bend-left.json"), encoding="utf-8") as handle:
            self.assertEqual(
                list(json.load(handle).items()),
                [("en", "Bend (left)"), ("cs", "Zatáčka vlevo"), ("sk", "Zákruta (vľavo)")],
            )

    def test_reports_page_problems_as_errors(self):
        self.write_page(SK_WIKITEXT.replace("</gallery>", "Súbor:Bez kódu.svg|Značka bez kódu\n</gallery>"))
        self.assertEqual(self.run_pipeline("--no-images"), 1)


class PruneTest(SandboxTestCase):
    def remove_danger_from_page(self):
        self.write_page(SK_WIKITEXT.replace("Súbor:101 Nebezpečenstvo.svg|101 Nebezpečenstvo\n", ""))

    def test_removes_signs_that_left_the_page(self):
        self.run_pipeline("--no-images")
        self.remove_danger_from_page()
        self.assertEqual(self.run_pipeline("--no-images"), 0)  # without --prune it only reports
        self.assertTrue(os.path.isdir(self.path("warning", "danger", "sk")))
        self.assertEqual(self.run_pipeline("--no-images", "--prune"), 0)
        self.assertFalse(os.path.exists(self.path("warning", "danger")))
        self.assertTrue(os.path.isdir(self.path("warning", "bend-left", "sk")))

    def test_keeps_a_sign_other_countries_still_have(self):
        self.run_pipeline("--no-images")
        os.makedirs(self.path("warning", "danger", "cz"))
        layout.update_translations("warning", "danger", {"cs": "Jiné nebezpečí"})
        self.remove_danger_from_page()
        self.assertEqual(self.run_pipeline("--no-images", "--prune"), 0)
        self.assertEqual(layout.country_dirs("warning", "danger"), ["cz"])
        self.assertEqual(layout.read_translations("warning", "danger"), {"en": "Other danger", "cs": "Jiné nebezpečí"})


class ImageTest(SandboxTestCase):
    SVG = b"<svg xmlns='http://www.w3.org/2000/svg'/>"

    def image_info(self, api, titles):
        if "commons" not in api:
            return {}
        return {
            t: {
                "title": t,
                "url": "https://upload.wikimedia.org/x.svg",
                "description_url": "https://commons.wikimedia.org/wiki/" + t,
                "sha1": hashlib.sha1(self.SVG).hexdigest(),
                "mime": "image/svg+xml",
                "license": "Public domain",
                "license_url": None,
                "author": "Ministerstvo dopravy a výstavby SR",
            }
            for t in titles
        }

    def test_downloads_images_only_when_sha1_changes(self):
        with mock.patch.object(Client, "image_info", side_effect=self.image_info), mock.patch.object(
            Client, "get", return_value=self.SVG
        ) as get:
            self.assertEqual(self.run_pipeline(), 0)
            self.assertEqual(get.call_count, 3)
            with open(self.path("warning", "danger", "sk", "danger-sk.svg"), "rb") as handle:
                self.assertEqual(handle.read(), self.SVG)
            with open(self.path("warning", "danger", "sk", "danger-sk.json"), encoding="utf-8") as handle:
                image = json.load(handle)["image"]
            self.assertEqual((image["file"], image["license"]), ("danger-sk.svg", "Public domain"))

            get.reset_mock()
            self.assertEqual(self.run_pipeline(), 0)
            get.assert_not_called()

    def test_missing_image_is_an_error(self):
        with mock.patch.object(Client, "image_info", return_value={}):
            self.assertEqual(self.run_pipeline(), 1)
