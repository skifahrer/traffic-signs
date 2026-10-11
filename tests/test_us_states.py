"""US states: route shields read from Wikipedia's road data modules, run as one bundle."""

import json
import unittest
from unittest import mock

from pipelines.__main__ import main
from pipelines.countries import all_sources, bundles, choices
from pipelines.countries.us_states import STATES
from pipelines.countries.us_states.parser import shield_parser

MODULE = """
local CA = {}
CA.SR = {
	base = "California State Route %route%",
	shield = "California %route%.svg",
	shieldmain = {
		["162"] = {"California %route%.svg", "Forest Route 7.svg"},
		default = "California %route%.svg"
	},
	name = {
		["162"] = "State Route %route% and<br>Forest Highway 7",
		default = "State Route %route%"
	},
}
CA.CA = CA.SR
CA.US = {
	shield = "US %route% (CA).svg",
}
return CA
"""


class ShieldParserTest(unittest.TestCase):
    def parse(self, text, state="CA", route="1"):
        return shield_parser(state, route)(text)

    def test_follows_the_state_type_to_its_shield(self):
        entries, problems = self.parse(MODULE, route="99")
        self.assertEqual(problems, [])
        self.assertEqual([(e.code, e.file, e.name) for e in entries], [("SR", "California 99.svg", "State Route 99")])

    def test_reads_a_shield_that_widens_with_the_number(self):
        text = """
CO.SH = {
	shield = {
		hook = "splitlen",
		split = 3,
		above = "Colorado %route% wide.svg",
		below = "Colorado %route%.svg",
	},
	name = "State Highway %route%",
}
CO.CO = CO.SH
"""
        entries, _ = self.parse(text, "CO")
        self.assertEqual(entries[0].file, "Colorado 1.svg")

    def test_reads_a_shield_of_another_type(self):
        text = """
MI.M = {
	shield = "M-%route%.svg",
	name = "M-%route%",
}
MI.MI = {
	shield = MI.M.shield,
	name = MI.M.name,
}
"""
        entries, _ = self.parse(text, "MI")
        self.assertEqual([(e.code, e.file, e.name) for e in entries], [("MI", "M-1.svg", "M-1")])

    def test_reports_a_module_without_a_state_route(self):
        entries, problems = self.parse("local XX = {}\nreturn XX", "XX")
        self.assertEqual(entries, [])
        self.assertEqual(len(problems), 1)


class BundleTest(unittest.TestCase):
    def test_states_are_regions_run_as_one_bundle(self):
        sources = all_sources()
        self.assertEqual(len(STATES), 52)
        self.assertEqual(sorted(bundles(sources)["us-states"]), sorted(f"us-{code}" for code in STATES))
        self.assertIn("us-states", choices(sources))
        self.assertNotIn("us-ca", choices(sources))
        self.assertEqual(sources["us-ca"].local_name_column, "name_en-US-CA")

    def test_matrix_runs_the_bundle_as_one_job(self):
        with mock.patch("builtins.print") as printed:
            self.assertEqual(main(["us-states", "--matrix"]), 0)
        self.assertEqual(json.loads(printed.call_args.args[0]), ["us-states"])


if __name__ == "__main__":
    unittest.main()
