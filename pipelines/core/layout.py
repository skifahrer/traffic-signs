"""Repository layout shared by all pipelines.

    signs/<category>/<sign>/<sign>.json                         names of the sign, keyed by language
    signs/<category>/<sign>/<country>/<sign>-<country>.<ext>    image (svg, png, ...)
    signs/<category>/<sign>/<country>/<sign>-<country>-archived-<year>.<ext>
                                                                an earlier image, valid until <year>
    signs/<category>/<sign>/<country>/<sign>-<country>.json     metadata and image provenance

The names file is shared by every country that has the sign, so pipelines
merge their languages into it instead of overwriting it.
"""

from __future__ import annotations

import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIGNS_DIR = os.path.join(REPO_ROOT, "signs")

# Top-level types. Keep this list short and country-neutral; country-specific
# groupings belong in the sign's metadata, not in the folder tree.
CATEGORIES = {
    "warning": "Warning signs",
    "regulatory": "Regulatory signs (priority, prohibitory, mandatory, parking)",
    "information": "Information, direction and lane signs",
    "additional-panel": "Additional panels placed below another sign",
    "traffic-device": "Barriers, direction boards, cones and other guiding devices",
    "traffic-signal": "Traffic lights and their supplementary devices",
}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COUNTRY_RE = re.compile(r"^[a-z]{2}(?:-[a-z0-9]{1,3})?$")  # ISO 3166-1 alpha-2, or 3166-2 for a region: "us-ca"


def sign_dir(category: str, slug: str, country: str) -> str:
    return os.path.join(SIGNS_DIR, category, slug, country)


def sign_path(category: str, slug: str, country: str, ext: str) -> str:
    return os.path.join(sign_dir(category, slug, country), f"{slug}-{country}.{ext}")


def archived_path(category: str, slug: str, country: str, ext: str, year: int) -> str:
    """A free name for an archived image: <sign>-<country>-archived-<year>[-<n>].<ext>."""
    base = os.path.join(sign_dir(category, slug, country), f"{slug}-{country}-archived-{year}")
    path, n = f"{base}.{ext}", 2
    while os.path.exists(path):
        path, n = f"{base}-{n}.{ext}", n + 1
    return path


def translations_path(category: str, slug: str) -> str:
    return os.path.join(SIGNS_DIR, category, slug, f"{slug}.json")


def read_translations(category: str, slug: str) -> dict[str, str]:
    path = translations_path(category, slug)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _ordered(names: dict[str, str]) -> dict[str, str]:
    """English first, then the other languages alphabetically."""
    return {lang: names[lang] for lang in sorted(names, key=lambda lang: (lang != "en", lang))}


def update_translations(category: str, slug: str, names: dict[str, str]) -> bool:
    """Merge `names` into the sign's names file, keeping other languages. True on change."""
    merged = _ordered({**read_translations(category, slug), **names})
    return write_json(translations_path(category, slug), merged)


def remove_translation(category: str, slug: str, lang: str) -> None:
    names = read_translations(category, slug)
    if names.pop(lang, None) is not None:
        write_json(translations_path(category, slug), _ordered(names))


def country_dirs(category: str, slug: str) -> list[str]:
    folder = os.path.join(SIGNS_DIR, category, slug)
    if not os.path.isdir(folder):
        return []
    return sorted(d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d)))


def validate(category: str, slug: str, country: str) -> None:
    if category not in CATEGORIES:
        raise ValueError(f"unknown category {category!r}")
    if not SLUG_RE.match(slug):
        raise ValueError(f"bad sign slug {slug!r}: use lowercase a-z, 0-9 and single hyphens")
    if not COUNTRY_RE.match(country):
        raise ValueError(f"bad country code {country!r}: use ISO 3166-1 alpha-2 (or 3166-2 for a region), lowercase")


def write_text(path: str, text: str) -> bool:
    """Write `text` if it differs from what is on disk. Returns True on change."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            if handle.read() == text:
                return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return True


def write_json(path: str, data: dict) -> bool:
    return write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def existing_signs(country: str, pipeline: str) -> dict[str, str]:
    """Metadata paths of the signs a pipeline previously wrote, keyed by `category/slug`."""
    found = {}
    if not os.path.isdir(SIGNS_DIR):
        return found
    for category in sorted(os.listdir(SIGNS_DIR)):
        category_dir = os.path.join(SIGNS_DIR, category)
        if not os.path.isdir(category_dir):
            continue
        for slug in sorted(os.listdir(category_dir)):
            meta = sign_path(category, slug, country, "json")
            if not os.path.exists(meta):
                continue
            with open(meta, encoding="utf-8") as handle:
                if json.load(handle).get("source", {}).get("pipeline") == pipeline:
                    found[f"{category}/{slug}"] = meta
    return found
