"""The OSM pipeline: which tagged values have an image, read offline from fake taginfo and wiki."""

import json
import os
import tempfile
import unittest
from unittest import mock

from pipelines import osm
from pipelines.osm import __main__ as osm_main


def sign(root, category, slug, country, code):
    d = os.path.join(root, category, slug, country)
    os.makedirs(d)
    with open(os.path.join(d, f"{slug}-{country}.json"), "w", encoding="utf-8") as f:
        json.dump({"sign": slug, "category": category, "country": country, "code": code}, f)


class FakeClient:
    """Answers taginfo and the wiki from a table, by key and query."""

    def __init__(self, values):
        self.values = values

    def get(self, url, params=None, post=None):
        if url == osm.WIKI_API:
            text = "{{Tag|traffic_sign|city_limit}} {{Tag|traffic_sign|stop}} {{Tag|traffic_sign|maxspeed}}"
            return json.dumps({"parse": {"wikitext": {"*": text}}}).encode()
        rows = [r for r in self.values.get(params["key"], [])
                if r[0].startswith(params.get("query", ""))]
        data = [{"value": v, "count": n} for v, n in rows]
        return json.dumps({"data_until": "2026-10-12", "total": len(data), "data": data}).encode()


class Components(unittest.TestCase):
    def test_signs_and_panels_carry_their_country(self):
        self.assertEqual(osm.components("DE:274[50],1020-30;city_limit"),
                         ["DE:274[50]", "DE:1020-30", "city_limit"])

    def test_a_comma_in_a_value_does_not_split(self):
        self.assertEqual(osm.components("SK:262[3,5],SK:506"), ["SK:262[3,5]", "SK:506"])


class Spelling(unittest.TestCase):
    def test_both_sides_read_alike(self):
        self.assertEqual(osm.spelled("hu", "A7"), osm.spelled("hu", "A-007"))
        self.assertEqual(osm.spelled("at", "52.10a"), osm.spelled("at", "§52 Z10a"))
        self.assertEqual(osm.spelled("cz", "P 6"), "p6")


class Match(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.tmp.name
        sign(root, "regulatory", "speed-limit-50", "sk", "253-50")
        sign(root, "regulatory", "give-way", "sk", "201")
        sign(root, "regulatory", "stop", "sk", "202")
        sign(root, "regulatory", "maximum-weight-7-5t", "sk", "240-7,5")
        self.signs = osm.Collection.read("sk", root)
        self.aliases = {("sk", "p1"): "201"}

    def test_a_value_needs_its_own_image(self):
        self.assertEqual(osm.match("SK:253[50]", self.signs, self.aliases, set()),
                         "regulatory/speed-limit-50")
        self.assertIsNone(osm.match("SK:253[45]", self.signs, self.aliases, set()))

    def test_an_old_code_goes_through_its_alias(self):
        self.assertEqual(osm.match("SK:P1", self.signs, self.aliases, set()), "regulatory/give-way")

    def test_another_country_is_not_ours(self):
        self.assertIsNone(osm.match("CZ:201", self.signs, self.aliases, set()))

    def test_the_summary_keeps_what_osm_has_and_lists_the_rest(self):
        got = osm.summarise("sk", {"SK:P1": 9, "SK:B34": 4}, {"stop": 100, "city_limit": 50},
                            self.signs, self.aliases, {})
        self.assertEqual(got["signs"]["SK:P1"], {"sign": "regulatory/give-way", "count": 9})
        self.assertEqual(got["signs"]["stop"], {"sign": "regulatory/stop", "count": 100})
        self.assertEqual(got["unmatched"], {"SK:B34": 4})
        self.assertEqual(got["human_without_image"], ["city_limit"])
        self.assertEqual(got["figures"], {"maxspeed": {"50": "regulatory/speed-limit-50"},
                                          "maxweight": {"7-5": "regulatory/maximum-weight-7-5t"}})
        self.assertEqual(got["implied"], {"stop": "regulatory/stop", "give_way": "regulatory/give-way"})


class Main(unittest.TestCase):
    def test_writes_one_file_per_country(self):
        with tempfile.TemporaryDirectory() as root:
            signs = os.path.join(root, "signs")
            sign(signs, "regulatory", "stop", "sk", "202")
            client = FakeClient({"traffic_sign": [("SK:202", 7), ("SK:B1", 3), ("stop", 90)]})
            out = os.path.join(root, "osm")
            with mock.patch.object(osm.layout, "SIGNS_DIR", signs), \
                    mock.patch.object(osm_main, "OSM_DIR", out), \
                    mock.patch.object(osm_main, "Client", return_value=client), \
                    mock.patch("builtins.print"):
                self.assertEqual(osm_main.main(["sk"]), 0)
            with open(os.path.join(out, "sk.json"), encoding="utf-8") as f:
                got = json.load(f)
        self.assertEqual(got["signs"]["SK:202"]["count"], 7)
        self.assertEqual(got["signs"]["stop"]["count"], 90)
        self.assertEqual(got["unmatched"], {"SK:B1": 3})


if __name__ == "__main__":
    unittest.main()
