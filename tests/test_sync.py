import datetime
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
    """Images follow Commons: downloaded when missing or changed, archived when gone."""

    YEAR = datetime.date.today().year
    OLD = b"<svg xmlns='http://www.w3.org/2000/svg'><!-- old --></svg>"
    NEW = b"<svg xmlns='http://www.w3.org/2000/svg'><!-- new --></svg>"

    def setUp(self):
        super().setUp()
        files = ("101 Nebezpečenstvo.svg", "110-10 Zákruta (vľavo).svg", "240-8,5 Maximálna hmotnosť (8,5 t).svg")
        self.commons = {f"File:{name}": self.OLD for name in files}  # what Commons has right now
        self.downloads = []
        for patch in (
            mock.patch.object(Client, "image_info", side_effect=self.image_info),
            mock.patch.object(Client, "get", side_effect=self.get),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def image_info(self, api, titles):
        if "commons" not in api:
            return {}
        return {
            t: {
                "title": t,
                "url": "https://upload.wikimedia.org/" + t,
                "description_url": "https://commons.wikimedia.org/wiki/" + t,
                "sha1": hashlib.sha1(self.commons[t]).hexdigest(),
                "mime": "image/svg+xml",
                "license": "Public domain",
                "license_url": None,
                "author": "Ministerstvo dopravy a výstavby SR",
            }
            for t in titles
            if t in self.commons
        }

    def get(self, url):
        title = url.split("upload.wikimedia.org/", 1)[1]
        self.downloads.append(title)
        return self.commons[title]

    def danger(self, name="danger-sk.json"):
        path = self.path("warning", "danger", "sk", name)
        if name.endswith(".json"):
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        with open(path, "rb") as handle:
            return handle.read()

    def test_downloads_missing_images_once(self):
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(len(self.downloads), 3)
        self.assertEqual(self.danger("danger-sk.svg"), self.OLD)
        image = self.danger()["image"]
        self.assertEqual((image["file"], image["license"]), ("danger-sk.svg", "Public domain"))

        self.downloads.clear()
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(self.downloads, [])

    def test_a_corrupt_download_is_fetched_again(self):
        corrupt = {"101 Nebezpečenstvo.svg": 1}  # the first transfer of this file arrives damaged
        original = self.get

        def flaky(url):
            data = original(url)
            name = url.rsplit("File:", 1)[-1]
            if corrupt.get(name):
                corrupt[name] -= 1
                return data[:-5]
            return data

        with mock.patch.object(Client, "get", side_effect=flaky):
            self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(self.danger("danger-sk.svg"), self.OLD)
        self.assertEqual(self.downloads.count("File:101 Nebezpečenstvo.svg"), 2)

    def test_an_image_that_never_matches_its_sha1_is_not_written(self):
        self.run_pipeline()
        self.commons["File:101 Nebezpečenstvo.svg"] = self.NEW
        original = self.get
        with mock.patch.object(Client, "get", side_effect=lambda url: original(url) + b"garbage"):
            self.assertEqual(self.run_pipeline(), 1)  # an error: the SHA-1 never matched
        self.assertEqual(self.danger("danger-sk.svg"), self.OLD)  # the old drawing stays
        self.assertFalse(os.path.exists(self.path("warning", "danger", "sk", "danger-sk.svg.part")))
        # The next run tries again, and succeeds once Commons sends the right bytes.
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(self.danger("danger-sk.svg"), self.NEW)

    def test_downloads_a_new_version_over_the_old_one(self):
        self.run_pipeline()
        self.commons["File:101 Nebezpečenstvo.svg"] = self.NEW
        self.downloads.clear()
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(self.downloads, ["File:101 Nebezpečenstvo.svg"])
        self.assertEqual(self.danger("danger-sk.svg"), self.NEW)
        self.assertEqual(self.danger()["image"]["sha1"], hashlib.sha1(self.NEW).hexdigest())
        self.assertNotIn("archived", self.danger())

    def test_archives_an_image_removed_from_commons(self):
        self.run_pipeline()
        del self.commons["File:101 Nebezpečenstvo.svg"]
        self.assertEqual(self.run_pipeline("--check"), 0)
        self.assertEqual(self.danger("danger-sk.svg"), self.OLD)  # --check renames nothing

        self.assertEqual(self.run_pipeline(), 0)
        archived_name = f"danger-sk-archived-{self.YEAR}.svg"
        self.assertEqual(set(os.listdir(self.path("warning", "danger", "sk"))), {"danger-sk.json", archived_name})
        self.assertEqual(self.danger(archived_name), self.OLD)
        meta = self.danger()
        self.assertNotIn("image", meta)
        self.assertNotIn("valid_until", meta)  # the sign itself is still on the page
        self.assertEqual(meta["archived"][0]["file"], archived_name)
        self.assertEqual(meta["archived"][0]["valid_until"], self.YEAR)
        self.assertEqual(meta["archived"][0]["sha1"], hashlib.sha1(self.OLD).hexdigest())

        before = self.snapshot()
        self.assertEqual(self.run_pipeline(), 0)  # still missing: no error, nothing archived twice
        self.assertEqual(self.snapshot(), before)

    def test_archives_a_sign_that_left_the_page_and_restores_it_when_it_returns(self):
        self.run_pipeline()
        self.write_page(SK_WIKITEXT.replace("Súbor:101 Nebezpečenstvo.svg|101 Nebezpečenstvo\n", ""))
        self.assertEqual(self.run_pipeline(), 0)
        archived_name = f"danger-sk-archived-{self.YEAR}.svg"
        meta = self.danger()
        self.assertEqual(meta["valid_until"], self.YEAR)
        self.assertNotIn("image", meta)
        self.assertEqual([a["file"] for a in meta["archived"]], [archived_name])
        self.assertEqual(layout.read_translations("warning", "danger")["sk"], "Nebezpečenstvo")  # names stay

        before = self.snapshot()
        self.assertEqual(self.run_pipeline(), 0)  # already archived: left alone
        self.assertEqual(self.snapshot(), before)

        self.write_page(SK_WIKITEXT)
        self.commons["File:101 Nebezpečenstvo.svg"] = self.NEW
        self.assertEqual(self.run_pipeline(), 0)
        meta = self.danger()
        self.assertNotIn("valid_until", meta)
        self.assertEqual(meta["image"]["file"], "danger-sk.svg")
        self.assertEqual(self.danger("danger-sk.svg"), self.NEW)
        self.assertEqual([a["file"] for a in meta["archived"]], [archived_name])

    def test_unknown_image_is_an_error(self):
        self.commons.clear()
        self.assertEqual(self.run_pipeline(), 1)
