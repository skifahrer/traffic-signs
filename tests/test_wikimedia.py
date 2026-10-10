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


class StripMarkupTest(unittest.TestCase):
    def test_links_and_formatting(self):
        self.assertEqual(strip_markup("[[Bratislava|Bratislave]] '''tučné''' &amp; <b>x</b>"), "Bratislave tučné & x")


if __name__ == "__main__":
    unittest.main()
