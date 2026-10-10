"""The viewer's data file: every sign with its names and each country's image.

    {
      "categories": {"warning": "Warning signs", ...},
      "countries": {"sk": {"name": "Slovakia", "language": "sk", "language_name": "Slovak"}, ...},
      "signs": [
        {"category": "warning", "sign": "danger",
         "names": {"en": "Other danger", "sk": "Nebezpečenstvo"},
         "countries": {"sk": {"code": "101", "image": "signs/warning/danger/sk/danger-sk.svg",
                              "license": ..., "author": ..., "source": ..., "valid_until": 2026,
                              "archived": [{"image": ..., "valid_until": 2026}]}}}
      ]
    }

Image paths are relative to the site root, where the builder copies signs/.
Formats browsers cannot show (TIFF) point at the PNG thumbnail that the
image's wiki renders instead.
"""

from __future__ import annotations

import json
import os
from urllib.parse import quote

from pipelines.core import layout
from pipelines.core.images import WEB_IMAGE_EXTS
from pipelines.countries import all_sources


def build_index() -> dict:
    sources = all_sources()
    countries: dict[str, dict] = {}
    signs = []
    for category in sorted(layout.CATEGORIES):
        category_dir = os.path.join(layout.SIGNS_DIR, category)
        if not os.path.isdir(category_dir):
            continue
        for slug in sorted(os.listdir(category_dir)):
            per_country = {}
            for country in layout.country_dirs(category, slug):
                meta_path = layout.sign_path(category, slug, country, "json")
                if not os.path.exists(meta_path):
                    continue
                with open(meta_path, encoding="utf-8") as handle:
                    per_country[country] = _country_entry(category, slug, country, json.load(handle))
                if country not in countries:
                    source = sources.get(country)
                    countries[country] = (
                        {"name": source.country_name, "language": source.language, "language_name": source.language_name}
                        if source
                        else {"name": country.upper(), "language": None, "language_name": None}
                    )
            if per_country:
                signs.append(
                    {
                        "category": category,
                        "sign": slug,
                        "names": layout.read_translations(category, slug),
                        "countries": per_country,
                    }
                )
    return {
        "categories": dict(layout.CATEGORIES),
        "countries": dict(sorted(countries.items())),
        "signs": signs,
    }


THUMBNAIL_WIDTH = 320  # px; the detail view shows images up to about 11rem high


def thumbnail_url(source: str | None) -> str | None:
    """The wiki's rendering of a file as a web image, from its description page URL.

    https://commons.wikimedia.org/wiki/File:X.tif → …/wiki/Special:FilePath/X.tif?width=320
    """
    if not source or "/wiki/File:" not in source:
        return None
    site, name = source.split("/wiki/File:", 1)
    return f"{site}/wiki/Special:FilePath/{quote(name, safe='%')}?width={THUMBNAIL_WIDTH}"


def _country_entry(category: str, slug: str, country: str, meta: dict) -> dict:
    def path(image: dict) -> str | None:
        file = image.get("file")
        if not file:
            return None
        if file.rsplit(".", 1)[-1].lower() not in WEB_IMAGE_EXTS:
            return thumbnail_url(image.get("source"))
        return f"signs/{category}/{slug}/{country}/{file}"

    image = meta.get("image") or {}
    entry = {
        "code": meta.get("code"),
        "image": path(image),
        "license": image.get("license"),
        "author": image.get("author"),
        "source": image.get("source"),
    }
    if "valid_until" in meta:
        entry["valid_until"] = meta["valid_until"]
    archived = [{"image": path(a), "valid_until": a.get("valid_until")} for a in meta.get("archived", [])]
    if archived:
        entry["archived"] = archived
    return entry
