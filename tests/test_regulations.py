"""Checks every file under regulations/ against the shape described in README.md."""

import json
import os
import re
import unittest

from pipelines.core import layout

REGULATIONS_DIR = os.path.join(layout.REPO_ROOT, "regulations")
CONTEXTS = {"urban", "rural", "motorway", "urban_motorway", "motorroad", "urban_motorroad", "living_street"}
VEHICLES = {"default", "motorcycle", "bus", "hgv", "trailer"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def speed_ok(value):
    return value is None or (type(value) is int and 5 <= value <= 200)


class RegulationsTest(unittest.TestCase):
    def test_regulations_tree(self):
        names = sorted(os.listdir(REGULATIONS_DIR))
        self.assertTrue(names, "regulations/ is empty")
        problems = []
        for name in names:
            country, ext = os.path.splitext(name)
            if ext != ".json" or not layout.COUNTRY_RE.match(country):
                problems.append(f"{name}: expected <country>.json")
                continue
            with open(os.path.join(REGULATIONS_DIR, name), encoding="utf-8") as handle:
                doc = json.load(handle)
            if doc.get("country") != country:
                problems.append(f"{name}: country {doc.get('country')!r} does not match the name")
            if doc.get("unit", "km/h") not in ("km/h", "mph"):
                problems.append(f"{name}: unknown unit {doc['unit']!r}")
            law = doc.get("law") or {}
            if not (law.get("name") and law.get("url", "").startswith("https://")
                    and DATE_RE.match(law.get("version", ""))):
                problems.append(f"{name}: law needs name, an https url and a YYYY-MM-DD version")
            speed = doc.get("speed") or {}
            if set(speed) != CONTEXTS:
                problems.append(f"{name}: contexts {sorted(set(speed) ^ CONTEXTS)} missing or unknown")
            for context, limit in speed.items():
                if "default" not in limit or not limit.get("section"):
                    problems.append(f"{name}: {context} needs default and section")
                for vehicle, value in limit.items():
                    if vehicle == "section":
                        continue
                    if vehicle not in VEHICLES or not speed_ok(value):
                        problems.append(f"{name}: {context}.{vehicle} = {value!r}")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
