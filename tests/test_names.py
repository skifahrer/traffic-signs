"""Checks the translations under names/ against the layout described in README.md."""

import json
import os
import re
import unittest

from pipelines.core import layout

NAMES_DIR = os.path.join(os.path.dirname(layout.SIGNS_DIR), "names")
# app language codes: sk, pt-BR, es-419, zh-Hans, sr-Latn-ME
CODE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-(?:[A-Z]{2}|\d{3}))?$")


class NamesTest(unittest.TestCase):
    def test_every_translation_names_a_sign(self):
        problems = []
        for file in sorted(os.listdir(NAMES_DIR)):
            if not file.endswith(".json") or not CODE_RE.match(file[:-5]):
                problems.append(f"names/{file}: expected names/<language code>.json")
                continue
            with open(os.path.join(NAMES_DIR, file), encoding="utf-8") as handle:
                names = json.load(handle)
            for sign, name in names.items():
                if not os.path.isfile(os.path.join(layout.SIGNS_DIR, sign, f"{sign.split('/')[-1]}.json")):
                    problems.append(f"names/{file}: {sign!r} is no sign folder")
                if not isinstance(name, str) or not name.strip() or name != name.strip():
                    problems.append(f"names/{file}: bad name for {sign!r}")
            if list(names) != sorted(names):
                problems.append(f"names/{file}: keys out of order")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
