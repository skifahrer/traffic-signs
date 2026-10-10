"""The sync engine shared by every country.

    read page → parse → apply corrections → match translations
      → fetch image metadata → write signs/ (names, metadata, images) → handle removed signs

A country only supplies a `Source` (see model.py); nothing in here is
country-specific.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field

from . import layout, log
from .model import Entry, Source, Translation
from .wikimedia import COMMONS_API, Client, sha1_of

IMAGE_EXTS = {"svg", "png", "jpg", "jpeg", "gif", "webp"}


@dataclass
class Options:
    check: bool = False  # report only, write nothing
    no_images: bool = False  # skip Commons metadata and image downloads
    prune: bool = False  # delete signs that are no longer on the page
    strict: bool = False  # fail when a sign has no translation
    wikitext: str | None = None  # read the page from this file instead of downloading it


@dataclass
class Result:
    source: Source
    options: Options
    entries: int = 0
    synced: int = 0
    unchanged: int = 0
    downloaded_bytes: int = 0
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    untranslated: list[Entry] = field(default_factory=list)
    renamed: list[str] = field(default_factory=list)
    unused: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return bool(self.errors or (self.options.strict and self.untranslated))

    def error(self, message: str) -> None:
        log.error(f"{self.source.country}: {message}")
        self.errors.append(message)


def sync(source: Source, client: Client, options: Options) -> Result:
    result = Result(source, options)
    mode = ", ".join(
        flag for flag, on in (("check only", options.check), ("no images", options.no_images), ("prune", options.prune)) if on
    )
    log.info(f"### {source.country_name} ({source.country}) from {source.page_url}" + (f" ({mode})" if mode else ""))

    with log.phase(f"{source.country}: read the list of signs"):
        signs = _read_signs(source, client, options, result)

    info: dict[str, dict] = {}
    if not options.no_images:
        with log.phase(f"{source.country}: fetch image metadata for {len(signs)} files"):
            info = _fetch_image_info(source, client, [entry.file for entry, _ in signs])

    previous = layout.existing_signs(source.country, source.pipeline)
    title = f"{source.country}: write {len(signs)} signs" + (" (check only, nothing is written)" if options.check else "")
    with log.phase(title):
        log.info(f"{len(previous)} signs from {source.country} already in signs/")
        progress = log.Progress(len(signs))
        for entry, translation in signs:
            _write_sign(source, client, options, result, previous, progress, entry, translation, info.get(entry.file))
        log.info(
            f"{len(result.added)} new, {len(result.changed)} changed, {result.unchanged} up to date,"
            f" {len(result.images)} images downloaded ({result.downloaded_bytes / 1024 / 1024:.1f} MB)"
        )

    result.removed = sorted(set(previous) - {f"{t.category}/{t.slug}" for _, t in signs})
    if result.removed:
        with log.phase(f"{source.country}: {len(result.removed)} signs no longer on the page"):
            _handle_removed(source, options, result.removed)
    return result


def _read_signs(source: Source, client: Client, options: Options, result: Result) -> list[tuple[Entry, Translation]]:
    """Parse the page and pair every entry with its translation."""
    if options.wikitext:
        log.info(f"Reading {options.wikitext}")
        with open(options.wikitext, encoding="utf-8") as handle:
            wikitext = handle.read()
    else:
        log.info(f"Downloading {source.page_url}")
        wikitext = client.page_wikitext(source.wiki, source.page)
    log.info(f"{len(wikitext):,} characters of wikitext")

    entries, problems = source.parser(wikitext)
    log.info(f"{len(entries)} entries with a sign code")
    for problem in problems:
        result.error(problem)
    for change in source.apply_corrections(entries):
        log.info(f"Correction applied: {change}")

    translations, problems = source.load_translations()
    log.info(f"{len(translations)} translations in {os.path.relpath(source.translations_file, layout.REPO_ROOT)}")
    for problem in problems:
        result.error(problem)

    by_code: dict[str, Entry] = {}
    for entry in entries:
        if entry.code in by_code:
            result.error(
                f"code {entry.code} appears twice: `{by_code[entry.code].file}` and `{entry.file}`"
                " (add a line to corrections.csv)"
            )
            continue
        by_code[entry.code] = entry

    signs = [(entry, translations[code]) for code, entry in by_code.items() if code in translations]
    result.entries, result.synced = len(by_code), len(signs)
    result.untranslated = [entry for code, entry in by_code.items() if code not in translations]
    result.unused = sorted(set(translations) - set(by_code))
    result.renamed = [
        f"`{e.code}`: translated from “{t.name_local}”, the page now says “{e.name}” (English: “{t.name_en}”)"
        for e, t in signs
        if e.name != t.name_local
    ]
    for entry in result.untranslated:
        log.warning(f"No translation for {entry.code} {entry.name}; skipped (add it to translations.csv)")
    for line in result.renamed:
        log.warning(f"Renamed on the page, check the English name: {line.replace('`', '')}")
    log.info(
        f"{len(signs)} signs to sync, {len(result.untranslated)} without translation,"
        f" {len(result.unused)} translations no longer on the page"
    )
    return signs


def _fetch_image_info(source: Source, client: Client, files: list[str]) -> dict[str, dict]:
    """imageinfo per file name, looking on Commons first, then on the local wiki."""
    titles = [f"File:{f}" for f in files]
    info = client.image_info(COMMONS_API, titles)
    log.info(f"Found {len(info)}/{len(titles)} files on Commons")
    missing = [t for t in titles if t not in info]
    if missing:
        local = client.image_info(source.api, missing)
        log.info(f"Found {len(local)}/{len(missing)} of the rest on {source.wiki}")
        info.update(local)
    return {title[len("File:"):]: value for title, value in info.items()}


def _write_sign(
    source: Source,
    client: Client,
    options: Options,
    result: Result,
    previous: dict[str, str],
    progress: log.Progress,
    entry: Entry,
    t: Translation,
    image: dict | None,
) -> None:
    country = source.country
    key = f"{t.category}/{t.slug}"
    label = f"{progress.step()} {entry.code} → {key}"
    meta_path = layout.sign_path(t.category, t.slug, country, "json")
    old_meta = _read_json(meta_path)

    ext = entry.file.rsplit(".", 1)[-1].lower()
    image_path = layout.sign_path(t.category, t.slug, country, ext)
    if image is None:
        if not options.no_images:
            result.error(f"{entry.code}: `{entry.file}` was not found on Commons or {source.wiki}")
        image_meta = (old_meta or {}).get("image")
    else:
        image_meta = {
            "file": os.path.basename(image_path),
            "sha1": image["sha1"],
            "source": image["description_url"],
            "author": image["author"],
            "license": image["license"],
            "license_url": image["license_url"],
        }

    meta = {
        "sign": t.slug,
        "category": t.category,
        "country": country,
        "code": entry.code,
        **({"image": image_meta} if image_meta else {}),
        "source": {"pipeline": source.pipeline, "page": source.page_url, "file": entry.file},
    }
    names = {"en": t.name_en, source.language: entry.name}
    old_names = layout.read_translations(t.category, t.slug)

    notes = []
    if key not in previous:
        result.added.append(f"`{key}` ← {entry.code} {entry.name}")
        notes.append("new")
    elif old_meta != meta or any(old_names.get(lang) != name for lang, name in names.items()):
        result.changed.append(f"`{key}` ({entry.code})")
        notes.append("metadata changed")
    needs_image = image is not None and sha1_of(image_path) != image["sha1"]
    if needs_image:
        notes.append("image " + ("outdated" if os.path.exists(image_path) else "missing"))

    if options.check:
        _log_sign(result, label, notes)
        return
    layout.update_translations(t.category, t.slug, names)
    layout.write_json(meta_path, meta)

    if needs_image:
        try:
            data = client.get(image["url"])
        except Exception as err:  # keep going; the report lists the failure
            result.error(f"{entry.code}: download of `{entry.file}` failed: {err}")
            return
        with open(image_path, "wb") as handle:
            handle.write(data)
        result.images.append(f"`{key}`")
        result.downloaded_bytes += len(data)
        notes[-1] = f"image downloaded ({len(data) / 1024:.1f} KB, ETA {progress.eta()})"
    for other in IMAGE_EXTS - {ext}:  # an image left over from an earlier file format
        stale = layout.sign_path(t.category, t.slug, country, other)
        if os.path.exists(stale):
            os.remove(stale)
            notes.append(f"removed old .{other} image")
    _log_sign(result, label, notes)


def _log_sign(result: Result, label: str, notes: list[str]) -> None:
    if notes:
        log.info(f"{label}: {', '.join(notes)}")
    else:
        result.unchanged += 1
        log.detail(f"{label}: up to date")


def _handle_removed(source: Source, options: Options, removed: list[str]) -> None:
    for key in removed:
        if not options.prune or options.check:
            log.warning(f"{key} is no longer on the page (run with --prune to delete it)")
            continue
        category, slug = key.split("/")
        _remove_dir(layout.sign_dir(category, slug, source.country))
        sign_folder = os.path.dirname(layout.translations_path(category, slug))
        if layout.country_dirs(category, slug):
            layout.remove_translation(category, slug, source.language)
            log.info(f"Deleted {key}/{source.country}; other countries keep the sign")
        elif os.path.isdir(sign_folder):
            _remove_dir(sign_folder)  # no other country has this sign: drop it with its names file
            log.info(f"Deleted {key}")


def _remove_dir(path: str) -> None:
    shutil.rmtree(path)
    parent = os.path.dirname(path)
    while parent != layout.SIGNS_DIR and os.path.isdir(parent) and not os.listdir(parent):
        os.rmdir(parent)
        parent = os.path.dirname(parent)


def _read_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
