"""Checks every file under signs/ against the layout described in README.md."""

import json
import os
import re
import unittest

from pipelines.core import layout

LANG_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")  # ISO 639, optionally with a region: de, de-AT
IMAGE_EXTS = {"svg", "png", "jpg", "jpeg", "gif", "webp"}


class LayoutTest(unittest.TestCase):
    def test_signs_tree(self):
        if not os.path.isdir(layout.SIGNS_DIR):
            self.skipTest("no signs/ yet")
        problems = []
        for dirpath, dirnames, filenames in os.walk(layout.SIGNS_DIR):
            parts = os.path.relpath(dirpath, layout.SIGNS_DIR).split(os.sep)
            if parts == ["."]:
                problems += [f"unknown category {d!r}" for d in dirnames if d not in layout.CATEGORIES]
                problems += [f"stray file signs/{f}" for f in filenames if f != "README.md"]
                continue
            if len(parts) == 1:
                problems += [f"stray file {parts[0]}/{f}" for f in filenames if f != "README.md"]
                continue
            if len(parts) == 2:
                category, slug = parts
                if not layout.SLUG_RE.match(slug):
                    problems.append(f"bad sign folder name {category}/{slug}")
                names_file = f"{slug}.json"
                problems += [
                    f"stray file {category}/{slug}/{f}" for f in filenames if f not in (names_file, "README.md")
                ]
                if names_file not in filenames:
                    problems.append(f"{category}/{slug}: missing names file {names_file}")
                    continue
                with open(os.path.join(dirpath, names_file), encoding="utf-8") as handle:
                    names = json.load(handle)
                if not isinstance(names, dict) or not names.get("en"):
                    problems.append(f"{category}/{slug}/{names_file}: needs an object with an \"en\" name")
                    continue
                for lang, name in names.items():
                    if not LANG_RE.match(lang) or not isinstance(name, str) or not name.strip():
                        problems.append(f"{category}/{slug}/{names_file}: bad entry {lang!r}")
                continue
            if len(parts) > 3:
                problems.append(f"too deep: {'/'.join(parts)}")
                continue
            category, slug, country = parts
            if not layout.COUNTRY_RE.match(country):
                problems.append(f"bad country folder {'/'.join(parts)}")
            prefix = f"{slug}-{country}."
            for name in filenames:
                where = f"{'/'.join(parts)}/{name}"
                if not name.startswith(prefix):
                    problems.append(f"{where}: name must start with {prefix}")
                    continue
                ext = name[len(prefix):]
                if ext == "json":
                    with open(os.path.join(dirpath, name), encoding="utf-8") as handle:
                        meta = json.load(handle)
                    if (meta.get("category"), meta.get("sign"), meta.get("country")) != (category, slug, country):
                        problems.append(f"{where}: category/sign/country do not match the path")
                elif ext not in IMAGE_EXTS:
                    problems.append(f"{where}: unknown extension .{ext} (names go in ../{slug}.json)")
        self.assertEqual(problems, [], "\n".join(problems[:50]))


if __name__ == "__main__":
    unittest.main()
