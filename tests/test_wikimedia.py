import unittest
from unittest import mock

from pipelines.wikimedia import Client, strip_markup


class ImageInfoTest(unittest.TestCase):
    def test_maps_normalised_titles_back_and_skips_missing_files(self):
        response = {
            "query": {
                "normalized": [{"from": "File:110-10_Zákruta.svg", "to": "File:110-10 Zákruta.svg"}],
                "pages": [
                    {
                        "title": "File:110-10 Zákruta.svg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/x.svg",
                                "descriptionurl": "https://commons.wikimedia.org/wiki/File:x.svg",
                                "sha1": "abc",
                                "mime": "image/svg+xml",
                                "extmetadata": {
                                    "LicenseShortName": {"value": "Public domain"},
                                    "Artist": {"value": "<a href='#'>Ministerstvo dopravy</a>"},
                                },
                            }
                        ],
                    },
                    {"title": "File:Missing.svg", "missing": True},
                ],
            }
        }
        client = Client()
        with mock.patch.object(client, "get_json", return_value=response):
            info = client.image_info("https://example.org/api.php", ["File:110-10_Zákruta.svg", "File:Missing.svg"])
        self.assertEqual(list(info), ["File:110-10_Zákruta.svg"])
        self.assertEqual(info["File:110-10_Zákruta.svg"]["sha1"], "abc")
        self.assertEqual(info["File:110-10_Zákruta.svg"]["author"], "Ministerstvo dopravy")
        self.assertEqual(info["File:110-10_Zákruta.svg"]["license"], "Public domain")


class RequestTest(unittest.TestCase):
    def test_api_queries_are_posted_so_long_title_lists_fit(self):
        titles = "|".join(f"File:{n} Tabuľový smerník na vyznačenie obchádzky (predbežný doľava).svg" for n in range(50))
        sent = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return b'{"query": {}}'

        def urlopen(request, timeout):
            sent["url"], sent["data"], sent["method"] = request.full_url, request.data, request.get_method()
            return Response()

        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            Client(delay=0).get_json("https://commons.wikimedia.org/w/api.php", {"action": "query", "titles": titles})
        self.assertEqual(sent["method"], "POST")
        self.assertEqual(sent["url"], "https://commons.wikimedia.org/w/api.php")
        self.assertGreater(len(sent["data"]), 4000)


class StripMarkupTest(unittest.TestCase):
    def test_links_and_formatting(self):
        self.assertEqual(strip_markup("[[Bratislava|Bratislave]] '''tučné''' &amp; <b>x</b>"), "Bratislave tučné & x")


if __name__ == "__main__":
    unittest.main()
