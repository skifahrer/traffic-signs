"""Checks every file under signs/ against the layout described in README.md."""

import json
import os
import re
import unittest

from pipelines import layout

LANG_RE = re.compile(r"^[a-z]{2,3}$")
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
            if len(parts) in (1, 2):
                problems += [f"stray file {'/'.join(parts)}/{f}" for f in filenames if f != "README.md"]
                if len(parts) == 2 and not layout.SLUG_RE.match(parts[1]):
                    problems.append(f"bad sign folder name {'/'.join(parts)}")
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
                elif ext not in IMAGE_EXTS and not LANG_RE.match(ext):
                    problems.append(f"{where}: unknown extension .{ext}")
        self.assertEqual(problems, [], "\n".join(problems[:50]))


if __name__ == "__main__":
    unittest.main()
