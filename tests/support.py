"""Shared test fixtures: a throwaway signs/ tree and sample pages."""

import os
import tempfile
import unittest
from unittest import mock

from pipelines.__main__ import main
from pipelines.core import layout

SK_WIKITEXT = """
== Zvislé dopravné značky ==
[[Súbor:Schilderwald Bratislava.JPG|right|thumb|Not in a gallery]]
<gallery style="text-align:center">
Súbor:101 Nebezpečenstvo.svg|101 Nebezpečenstvo
Súbor:110-10 Zákruta (vľavo).svg|110-10 Zákruta (vľavo)
Súbor:240-8,5 Maximálna hmotnosť (8,5 t).svg|240-5,5 Maximálna hmotnosť (8,5 t)
</gallery>
"""
SK_SIGNS = {"warning/danger", "warning/bend-left", "regulatory/maximum-weight-8-5t"}


class SandboxTestCase(unittest.TestCase):
    """Runs the pipeline against a temporary signs/ folder, with output silenced."""

    wikitext = SK_WIKITEXT

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.page = self.write_page(self.wikitext)
        for patch in (
            mock.patch.object(layout, "SIGNS_DIR", os.path.join(self.root, "signs")),
            mock.patch("builtins.print"),
        ):
            patch.start()
            self.addCleanup(patch.stop)
        self.addCleanup(self._tmp.cleanup)

    def write_page(self, wikitext: str) -> str:
        path = os.path.join(self.root, "page.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(wikitext)
        return path

    def run_pipeline(self, *args: str) -> int:
        return main(["sk", "--wikitext", self.page, *args])

    def path(self, *parts: str) -> str:
        return os.path.join(self.root, "signs", *parts)

    def snapshot(self) -> dict:
        """Modification times of every file under the sandbox."""
        return {
            os.path.join(d, f): os.path.getmtime(os.path.join(d, f)) for d, _, files in os.walk(self.root) for f in files
        }
