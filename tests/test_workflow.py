"""The sync workflow's country dropdown must list every country pipeline."""

import json
import os
import re
import unittest
from unittest import mock

from pipelines.__main__ import main
from pipelines.core import layout
from pipelines.countries import all_sources

WORKFLOW = os.path.join(layout.REPO_ROOT, ".github", "workflows", "sync.yml")


def dropdown_options() -> list[str]:
    """The `options:` of the `country` input, read without a YAML library."""
    with open(WORKFLOW, encoding="utf-8") as handle:
        text = handle.read()
    block = re.search(r"^ {6}country:\n(?:^ {8}.*\n)*?^ {8}options:\n((?:^ {10}- .*\n|^ *#.*\n)+)", text, re.MULTILINE)
    if not block:
        raise AssertionError("no `options:` list under the `country` input in sync.yml")
    return re.findall(r"^ {10}- (\S+)", block.group(1), re.MULTILINE)


class WorkflowTest(unittest.TestCase):
    def test_dropdown_lists_all_and_every_country(self):
        expected = ["all", *sorted(all_sources())]
        self.assertEqual(
            dropdown_options(),
            expected,
            "update the `country` options in .github/workflows/sync.yml",
        )

    def test_matrix_lists_the_countries_to_run(self):
        for choice, countries in (("all", sorted(all_sources())), ("sk", ["sk"])):
            with self.subTest(choice=choice), mock.patch("builtins.print") as printed:
                self.assertEqual(main([choice, "--matrix"]), 0)
                self.assertEqual(json.loads(printed.call_args.args[0]), countries)


if __name__ == "__main__":
    unittest.main()
