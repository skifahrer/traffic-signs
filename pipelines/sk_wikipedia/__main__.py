"""Sync Slovak traffic signs from the Slovak Wikipedia list into signs/.

Source: https://sk.wikipedia.org/wiki/Zoznam_dopravných_značiek_na_Slovensku

    python3 -m pipelines.sk_wikipedia               # update names, metadata and images
    python3 -m pipelines.sk_wikipedia --no-images   # names and metadata only
    python3 -m pipelines.sk_wikipedia --check       # report what would change, write nothing

Every gallery entry on the page ("Súbor:<file>|<code> <Slovak name>") becomes
one sign. English folder names come from translations.csv, keyed by the Slovak
sign code; a sign whose code is not in that file is reported and skipped until
someone adds a translation. corrections.csv fixes known mistakes in the page.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import urllib.parse
from dataclasses import dataclass

from .. import layout
from ..wikimedia import COMMONS_API, Client, sha1_of, strip_markup

COUNTRY = "sk"
LANG = "sk"
PIPELINE = "sk-wikipedia"
WIKI = "sk.wikipedia.org"
PAGE = "Zoznam dopravných značiek na Slovensku"
PAGE_URL = f"https://{WIKI}/wiki/" + urllib.parse.quote(PAGE.replace(" ", "_"))
LOCAL_API = f"https://{WIKI}/w/api.php"

HERE = os.path.dirname(os.path.abspath(__file__))
TRANSLATIONS = os.path.join(HERE, "translations.csv")
CORRECTIONS = os.path.join(HERE, "corrections.csv")

IMAGE_EXTS = {"svg", "png", "jpg", "jpeg", "gif", "webp"}
GALLERY_LINE = re.compile(r"^\s*(?:Súbor|File|Image|Obrázok)\s*:\s*([^|]+?)\s*\|(.*)$", re.IGNORECASE)
CAPTION = re.compile(r"^(\d{3}(?:-[0-9]+(?:,[0-9]+)?)*)\s+(.+)$")


@dataclass
class Entry:
    file: str  # file name without the namespace, e.g. "101 Nebezpečenstvo.svg"
    code: str  # Slovak sign code, e.g. "101" or "240-3,5"
    name: str  # Slovak name


@dataclass
class Translation:
    code: str
    category: str
    slug: str
    name_en: str
    name_sk: str  # the Slovak name the English one was translated from


def parse(wikitext: str) -> tuple[list[Entry], list[str]]:
    entries, problems = [], []
    in_gallery = False
    for line in wikitext.splitlines():
        if re.match(r"\s*<gallery\b", line, re.IGNORECASE):
            in_gallery = True
            continue
        if re.match(r"\s*</gallery>", line, re.IGNORECASE):
            in_gallery = False
            continue
        if not in_gallery:
            continue
        match = GALLERY_LINE.match(line)
        if not match:
            continue
        file, caption = match.group(1).replace("_", " "), strip_markup(match.group(2))
        parsed = CAPTION.match(caption)
        if not parsed:
            problems.append(f"caption without a sign code: `{file}` → `{caption}`")
            continue
        entries.append(Entry(file=file, code=parsed.group(1), name=parsed.group(2).strip()))
    return entries, problems


def read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if not row[next(iter(row))].startswith("#")]


def apply_corrections(entries: list[Entry]) -> None:
    fixes = {row["file"]: row for row in read_csv(CORRECTIONS)}
    for entry in entries:
        fix = fixes.get(entry.file)
        if fix:
            entry.code = fix["code"] or entry.code
            entry.name = fix["name_sk"] or entry.name


def load_translations() -> tuple[dict[str, Translation], list[str]]:
    translations, problems, seen = {}, [], {}
    for row in read_csv(TRANSLATIONS):
        t = Translation(row["code"], row["category"], row["slug"], row["name_en"], row["name_sk"])
        try:
            layout.validate(t.category, t.slug, COUNTRY)
        except ValueError as err:
            problems.append(f"translations.csv, code {t.code}: {err}")
            continue
        key = f"{t.category}/{t.slug}"
        if t.code in translations:
            problems.append(f"translations.csv lists code {t.code} twice")
        if key in seen:
            problems.append(f"translations.csv maps codes {seen[key]} and {t.code} to the same sign `{key}`")
        seen[key] = t.code
        translations[t.code] = t
    return translations, problems


def fetch_image_info(client: Client, files: list[str]) -> dict[str, dict]:
    """imageinfo per file name, looking on Commons first, then on sk.wikipedia."""
    titles = [f"File:{f}" for f in files]
    info = client.image_info(COMMONS_API, titles)
    missing = [t for t in titles if t not in info]
    if missing:
        info.update(client.image_info(LOCAL_API, missing))
    return {title[len("File:"):]: value for title, value in info.items()}


def remove_dir(path: str) -> None:
    shutil.rmtree(path)
    parent = os.path.dirname(path)
    while parent != layout.SIGNS_DIR and os.path.isdir(parent) and not os.listdir(parent):
        os.rmdir(parent)
        parent = os.path.dirname(parent)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--wikitext", help="read the page from this file instead of downloading it")
    parser.add_argument("--no-images", action="store_true", help="skip Commons metadata and image downloads")
    parser.add_argument("--check", action="store_true", help="report changes without writing anything")
    parser.add_argument("--prune", action="store_true", help="delete signs that are no longer on the page")
    parser.add_argument("--strict", action="store_true", help="fail when a sign has no translation")
    parser.add_argument("--report", help="also write the Markdown report to this file")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between Wikimedia requests")
    args = parser.parse_args(argv)

    client = Client(delay=args.delay)
    if args.wikitext:
        with open(args.wikitext, encoding="utf-8") as handle:
            wikitext = handle.read()
    else:
        print(f"Downloading {PAGE_URL}", file=sys.stderr)
        wikitext = client.page_wikitext(WIKI, PAGE)

    entries, errors = parse(wikitext)
    apply_corrections(entries)
    translations, translation_errors = load_translations()
    errors += translation_errors

    by_code: dict[str, Entry] = {}
    for entry in entries:
        if entry.code in by_code:
            errors.append(
                f"code {entry.code} appears twice: `{by_code[entry.code].file}` and `{entry.file}`"
                " (add a line to corrections.csv)"
            )
            continue
        by_code[entry.code] = entry

    untranslated = [e for code, e in by_code.items() if code not in translations]
    signs = [(by_code[code], translations[code]) for code in by_code if code in translations]
    unused = sorted(set(translations) - set(by_code))
    renamed = [
        f"`{e.code}`: translated from “{t.name_sk}”, the page now says “{e.name}” (English: “{t.name_en}”)"
        for e, t in signs
        if e.name != t.name_sk
    ]

    info: dict[str, dict] = {}
    if not args.no_images:
        print(f"Fetching image metadata for {len(signs)} files", file=sys.stderr)
        info = fetch_image_info(client, [entry.file for entry, _ in signs])

    previous = layout.existing_signs(COUNTRY, PIPELINE)
    current = {f"{t.category}/{t.slug}" for _, t in signs}
    added, changed, images = [], [], []
    for entry, t in signs:
        key = f"{t.category}/{t.slug}"
        meta_path = layout.sign_path(t.category, t.slug, COUNTRY, "json")
        old_meta = None
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as handle:
                old_meta = json.load(handle)

        image = info.get(entry.file)
        ext = entry.file.rsplit(".", 1)[-1].lower()
        image_name = f"{t.slug}-{COUNTRY}.{ext}"
        image_path = layout.sign_path(t.category, t.slug, COUNTRY, ext)
        if args.no_images or image is None:
            if not args.no_images:
                errors.append(f"{entry.code}: `{entry.file}` was not found on Commons or {WIKI}")
            image_meta = (old_meta or {}).get("image")
        else:
            image_meta = {
                "file": image_name,
                "sha1": image["sha1"],
                "source": image["description_url"],
                "author": image["author"],
                "license": image["license"],
                "license_url": image["license_url"],
            }

        meta = {
            "sign": t.slug,
            "category": t.category,
            "country": COUNTRY,
            "code": entry.code,
            "image": image_meta,
            "source": {"pipeline": PIPELINE, "page": PAGE_URL, "file": entry.file},
        }
        if image_meta is None:
            del meta["image"]

        names = {"en": t.name_en, LANG: entry.name}
        old_names = layout.read_translations(t.category, t.slug)
        if key not in previous:
            added.append(f"`{key}` ← {entry.code} {entry.name}")
        elif old_meta != meta or any(old_names.get(lang) != name for lang, name in names.items()):
            changed.append(f"`{key}` ({entry.code})")

        if args.check:
            continue
        layout.update_translations(t.category, t.slug, names)
        layout.write_json(meta_path, meta)

        if image is not None and sha1_of(image_path) != image["sha1"]:
            print(f"  {entry.code}: downloading {entry.file}", file=sys.stderr)
            try:
                data = client.get(image["url"])
            except Exception as err:  # keep going; the report lists the failure
                errors.append(f"{entry.code}: download of `{entry.file}` failed: {err}")
                continue
            with open(image_path, "wb") as handle:
                handle.write(data)
            images.append(f"`{key}`")
        # Drop an image left over from an earlier file format.
        for other in IMAGE_EXTS - {ext}:
            stale = layout.sign_path(t.category, t.slug, COUNTRY, other)
            if os.path.exists(stale):
                os.remove(stale)

    removed = sorted(set(previous) - current)
    if args.prune and not args.check:
        for key in removed:
            category, slug = key.split("/")
            remove_dir(layout.sign_dir(category, slug, COUNTRY))
            if layout.country_dirs(category, slug):
                layout.remove_translation(category, slug, LANG)
            elif os.path.isdir(sign_folder := os.path.dirname(layout.translations_path(category, slug))):
                remove_dir(sign_folder)  # no other country has this sign: drop it with its names file

    report = render_report(
        entries=len(by_code),
        synced=len(signs),
        added=added,
        changed=changed,
        images=images,
        removed=removed,
        pruned=args.prune,
        untranslated=untranslated,
        renamed=renamed,
        unused=unused,
        errors=errors,
    )
    print(report)
    if args.report:
        layout.write_text(args.report, report)
    if errors or (args.strict and untranslated):
        return 1
    return 0


def render_report(*, entries, synced, added, changed, images, removed, pruned, untranslated, renamed, unused, errors) -> str:
    lines = [
        f"## Slovak traffic signs from [Wikipedia]({PAGE_URL})",
        "",
        f"- Signs on the page: {entries}",
        f"- Synced (have a translation): {synced}",
        f"- New: {len(added)}, metadata changed: {len(changed)}, images downloaded: {len(images)}",
        f"- No longer on the page: {len(removed)}" + (" (deleted)" if pruned and removed else ""),
        f"- Waiting for a translation: {len(untranslated)}",
        "",
    ]

    def section(title: str, items: list[str], limit: int = 100) -> None:
        if items:
            shown = [f"- {item}" for item in items[:limit]]
            if len(items) > limit:
                shown.append(f"- … and {len(items) - limit} more")
            lines.extend([f"### {title}", "", *shown, ""])

    section("Errors", errors)
    section(
        "Missing translations (add them to pipelines/sk_wikipedia/translations.csv)",
        [f"`{e.code}` {e.name} (`{e.file}`)" for e in untranslated],
    )
    section("Slovak name changed, check the English translation", renamed)
    section("New signs", added)
    section("Changed metadata", changed)
    section("Removed from the page" + ("" if pruned else " (run with --prune to delete)"), [f"`{k}`" for k in removed])
    section("Translations whose code is no longer on the page", [f"`{c}`" for c in unused])
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
