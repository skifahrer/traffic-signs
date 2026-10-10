import hashlib
import json
import os
import re
import tempfile
import unittest
from unittest import mock

from pipelines import layout
from pipelines.sk_wikipedia import __main__ as sk

WIKITEXT = """
== Zvislé dopravné značky ==
[[Súbor:Schilderwald Bratislava.JPG|right|thumb|Not in a gallery]]
<gallery style="text-align:center">
Súbor:101 Nebezpečenstvo.svg|101 Nebezpečenstvo
Súbor:110-10 Zákruta (vľavo).svg|110-10 Zákruta (vľavo)
Súbor:240-8,5 Maximálna hmotnosť (8,5 t).svg|240-5,5 Maximálna hmotnosť (8,5 t)
Súbor:Bez kódu.svg|Značka bez kódu
</gallery>
"""
CLEAN_WIKITEXT = WIKITEXT.replace("Súbor:Bez kódu.svg|Značka bez kódu\n", "")


class ParseTest(unittest.TestCase):
    def test_reads_gallery_entries_only(self):
        entries, problems = sk.parse(WIKITEXT)
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

    def test_corrections_fix_wrong_codes(self):
        entries, _ = sk.parse(WIKITEXT)
        sk.apply_corrections(entries)
        self.assertEqual(entries[2].code, "240-8,5")


class TranslationsTest(unittest.TestCase):
    def test_translations_file_is_consistent(self):
        translations, problems = sk.load_translations()
        self.assertEqual(problems, [])
        self.assertGreater(len(translations), 800)
        for t in translations.values():
            self.assertTrue(t.name_en.strip(), t.code)
            self.assertTrue(re.match(r"^\d{3}", t.code), t.code)


class SyncTest(unittest.TestCase):
    def test_writes_layout_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            wikitext = os.path.join(root, "page.txt")
            with open(wikitext, "w", encoding="utf-8") as handle:
                handle.write(CLEAN_WIKITEXT)
            with mock.patch.object(layout, "SIGNS_DIR", os.path.join(root, "signs")), mock.patch(
                "builtins.print"
            ):
                self.assertEqual(sk.main(["--wikitext", wikitext, "--no-images"]), 0)
                folder = os.path.join(root, "signs", "warning", "bend-left", "sk")
                self.assertEqual(sorted(os.listdir(folder)), ["bend-left-sk.json"])
                with open(os.path.join(root, "signs", "warning", "bend-left", "bend-left.json"), encoding="utf-8") as handle:
                    self.assertEqual(json.load(handle), {"en": "Bend (left)", "sk": "Zákruta (vľavo)"})
                self.assertTrue(os.path.isdir(os.path.join(root, "signs", "regulatory", "maximum-weight-8-5t")))
                self.assertEqual(
                    set(layout.existing_signs("sk", sk.PIPELINE)),
                    {"warning/danger", "warning/bend-left", "regulatory/maximum-weight-8-5t"},
                )
                before = {
                    os.path.join(d, f): os.path.getmtime(os.path.join(d, f))
                    for d, _, files in os.walk(root)
                    for f in files
                }
                self.assertEqual(sk.main(["--wikitext", wikitext, "--no-images"]), 0)
                after = {
                    os.path.join(d, f): os.path.getmtime(os.path.join(d, f))
                    for d, _, files in os.walk(root)
                    for f in files
                }
                self.assertEqual(before, after)

    def test_prune_removes_signs_that_left_the_page(self):
        with tempfile.TemporaryDirectory() as root:
            wikitext = os.path.join(root, "page.txt")
            with open(wikitext, "w", encoding="utf-8") as handle:
                handle.write(CLEAN_WIKITEXT)
            with mock.patch.object(layout, "SIGNS_DIR", os.path.join(root, "signs")), mock.patch(
                "builtins.print"
            ):
                sk.main(["--wikitext", wikitext, "--no-images"])
                with open(wikitext, "w", encoding="utf-8") as handle:
                    handle.write(CLEAN_WIKITEXT.replace("Súbor:101 Nebezpečenstvo.svg|101 Nebezpečenstvo\n", ""))
                self.assertEqual(sk.main(["--wikitext", wikitext, "--no-images", "--prune"]), 0)
                self.assertFalse(os.path.exists(os.path.join(root, "signs", "warning", "danger")))
                self.assertTrue(os.path.isdir(os.path.join(root, "signs", "warning", "bend-left", "sk")))

    def test_downloads_images_only_when_sha1_changes(self):
        svg = b"<svg xmlns='http://www.w3.org/2000/svg'/>"
        info = {
            "title": "File:x.svg",
            "url": "https://upload.wikimedia.org/x.svg",
            "description_url": "https://commons.wikimedia.org/wiki/File:x.svg",
            "sha1": hashlib.sha1(svg).hexdigest(),
            "mime": "image/svg+xml",
            "license": "Public domain",
            "license_url": None,
            "author": "Ministerstvo dopravy a výstavby SR",
        }

        def image_info(api, titles):
            return {t: dict(info) for t in titles} if "commons" in api else {}

        with tempfile.TemporaryDirectory() as root:
            wikitext = os.path.join(root, "page.txt")
            with open(wikitext, "w", encoding="utf-8") as handle:
                handle.write(CLEAN_WIKITEXT)
            with mock.patch.object(layout, "SIGNS_DIR", os.path.join(root, "signs")), mock.patch(
                "builtins.print"
            ), mock.patch.object(sk.Client, "image_info", side_effect=image_info), mock.patch.object(
                sk.Client, "get", return_value=svg
            ) as get:
                self.assertEqual(sk.main(["--wikitext", wikitext]), 0)
                self.assertEqual(get.call_count, 3)
                image = os.path.join(root, "signs", "warning", "danger", "sk", "danger-sk.svg")
                with open(image, "rb") as handle:
                    self.assertEqual(handle.read(), svg)
                with open(image[:-3] + "json", encoding="utf-8") as handle:
                    meta = json.load(handle)
                self.assertEqual(meta["image"]["file"], "danger-sk.svg")
                self.assertEqual(meta["image"]["license"], "Public domain")

                get.reset_mock()
                self.assertEqual(sk.main(["--wikitext", wikitext]), 0)
                get.assert_not_called()

    def test_keeps_other_languages_in_the_names_file(self):
        with tempfile.TemporaryDirectory() as root:
            wikitext = os.path.join(root, "page.txt")
            with open(wikitext, "w", encoding="utf-8") as handle:
                handle.write(CLEAN_WIKITEXT)
            names = os.path.join(root, "signs", "warning", "bend-left", "bend-left.json")
            os.makedirs(os.path.dirname(names))
            with open(names, "w", encoding="utf-8") as handle:
                json.dump({"cs": "Zatáčka vlevo", "en": "Old English name"}, handle)
            with mock.patch.object(layout, "SIGNS_DIR", os.path.join(root, "signs")), mock.patch(
                "builtins.print"
            ):
                self.assertEqual(sk.main(["--wikitext", wikitext, "--no-images"]), 0)
            with open(names, encoding="utf-8") as handle:
                self.assertEqual(
                    list(json.load(handle).items()),
                    [("en", "Bend (left)"), ("cs", "Zatáčka vlevo"), ("sk", "Zákruta (vľavo)")],
                )

    def test_prune_keeps_a_sign_other_countries_still_have(self):
        with tempfile.TemporaryDirectory() as root:
            wikitext = os.path.join(root, "page.txt")
            with open(wikitext, "w", encoding="utf-8") as handle:
                handle.write(CLEAN_WIKITEXT)
            with mock.patch.object(layout, "SIGNS_DIR", os.path.join(root, "signs")), mock.patch(
                "builtins.print"
            ):
                sk.main(["--wikitext", wikitext, "--no-images"])
                os.makedirs(os.path.join(root, "signs", "warning", "danger", "cz"))
                layout.update_translations("warning", "danger", {"cs": "Jiné nebezpečí"})
                with open(wikitext, "w", encoding="utf-8") as handle:
                    handle.write(CLEAN_WIKITEXT.replace("Súbor:101 Nebezpečenstvo.svg|101 Nebezpečenstvo\n", ""))
                self.assertEqual(sk.main(["--wikitext", wikitext, "--no-images", "--prune"]), 0)
                self.assertEqual(layout.country_dirs("warning", "danger"), ["cz"])
                self.assertEqual(
                    layout.read_translations("warning", "danger"), {"en": "Other danger", "cs": "Jiné nebezpečí"}
                )


if __name__ == "__main__":
    unittest.main()
