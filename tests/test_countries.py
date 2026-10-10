import dataclasses
from unittest import mock

from pipelines import __main__ as cli
from pipelines.core import layout
from pipelines.countries import all_sources
from tests.support import SK_SIGNS, SandboxTestCase


class RegistryTest(SandboxTestCase):
    def test_every_country_has_consistent_translations(self):
        sources = all_sources()
        self.assertIn("sk", sources)
        for code, source in sources.items():
            with self.subTest(country=code):
                translations, problems = source.load_translations()
                self.assertEqual(problems, [])
                self.assertTrue(translations)
                for t in translations.values():
                    self.assertTrue(t.name_en.strip() and t.name_local.strip(), t.code)

    def test_shared_signs_agree_on_category_and_english_name(self):
        # The names file is shared, so two countries using the same folder
        # must not fight over its English name or put it in two categories.
        first: dict[str, tuple] = {}
        for code, source in all_sources().items():
            translations, _ = source.load_translations()
            for t in translations.values():
                seen = first.setdefault(t.slug, (t.category, t.name_en, code))
                with self.subTest(sign=t.slug, countries=(seen[2], code)):
                    self.assertEqual((t.category, t.name_en), seen[:2])

    def test_sk_codes_follow_the_national_pattern(self):
        translations, _ = all_sources()["sk"].load_translations()
        for code in translations:
            self.assertRegex(code, r"^\d{3}")


class CommandLineTest(SandboxTestCase):
    """`python -m pipelines` with a second, fake country next to Slovakia."""

    def setUp(self):
        super().setUp()
        sk = all_sources()["sk"]
        # "Zemlandia" reuses the Slovak data under another country code.
        self.zz = dataclasses.replace(sk, country="zz", country_name="Zemlandia")
        self.page_fetches = []
        patches = (
            mock.patch.object(cli, "all_sources", return_value={"sk": sk, "zz": self.zz}),
            mock.patch("pipelines.core.wikimedia.Client.page_wikitext", side_effect=self.fetch_page),
        )
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def fetch_page(self, wiki, title):
        self.page_fetches.append(wiki)
        with open(self.page, encoding="utf-8") as handle:
            return handle.read()

    def countries_in_signs(self):
        return {c for key in SK_SIGNS for c in layout.country_dirs(*key.split("/"))}

    def test_runs_every_country_by_default(self):
        self.assertEqual(cli.main(["--no-images"]), 0)
        self.assertEqual(self.countries_in_signs(), {"sk", "zz"})
        self.assertEqual(cli.main(["all", "--no-images", "--check"]), 0)

    def test_runs_only_the_selected_country(self):
        self.assertEqual(cli.main(["ZZ", "--no-images"]), 0)
        self.assertEqual(self.countries_in_signs(), {"zz"})
        self.assertEqual(len(self.page_fetches), 1)

    def test_one_failing_country_does_not_stop_the_others(self):
        broken = dataclasses.replace(self.zz, parser=mock.Mock(side_effect=RuntimeError("page layout changed")))
        with mock.patch.object(cli, "all_sources", return_value={"zz": broken, "sk": all_sources()["sk"]}):
            self.assertEqual(cli.main(["--no-images"]), 1)
        self.assertEqual(self.countries_in_signs(), {"sk"})

    def test_rejects_unknown_countries_and_ambiguous_wikitext(self):
        with mock.patch("sys.stderr"):
            for argv in (["xx"], ["sk", "zz", "--wikitext", self.page]):
                with self.subTest(argv=argv), self.assertRaises(SystemExit):
                    cli.main(argv)

    def test_list(self):
        self.assertEqual(cli.main(["--list"]), 0)
