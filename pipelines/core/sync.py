"""The sync engine shared by every country.

    read page → parse → apply corrections → match translations
      → fetch image metadata → write signs/ (names, metadata, images)
      → archive signs that left the page

A country only supplies a `Source` (see model.py); nothing in here is
country-specific.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
from dataclasses import dataclass, field

from . import images, layout, log
from .model import Entry, Source, Translation
from .wikimedia import COMMONS_API, Client


@dataclass
class Options:
    check: bool = False  # report only, write nothing
    no_images: bool = False  # skip Commons metadata and image downloads
    prune: bool = False  # delete signs that left the page instead of archiving them
    strict: bool = False  # fail when a sign has no translation
    wikitext: str | None = None  # read the page from this file instead of downloading it
    year: int = field(default_factory=lambda: datetime.date.today().year)  # "valid_until" of what gets archived


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
    archived: list[str] = field(default_factory=list)
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

    gone = sorted(set(previous) - {f"{t.category}/{t.slug}" for _, t in signs})
    # Signs archived by an earlier run stay as they are, unless --prune deletes them.
    result.removed = gone if options.prune else [key for key in gone if "valid_until" not in _read_json(previous[key])]
    if result.removed:
        with log.phase(f"{source.country}: {len(result.removed)} signs no longer on the page"):
            for key in result.removed:
                (_delete_sign if options.prune else _archive_sign)(source, options, result, key)
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

    entries, problems = source.parse(wikitext)
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
    info: dict | None,
) -> None:
    country = source.country
    key = f"{t.category}/{t.slug}"
    label = f"{progress.step()} {entry.code} → {key}"
    meta_path = layout.sign_path(t.category, t.slug, country, "json")
    old_meta = _read_json(meta_path) or {}
    ext = entry.file.rsplit(".", 1)[-1].lower()
    image_path = layout.sign_path(t.category, t.slug, country, ext)

    notes = []
    image_meta = old_meta.get("image")
    archived = list(old_meta.get("archived", []))
    download = None
    if info is not None:
        image_meta = images.image_meta(image_path, info)
        download = images.status(image_path, info)
    elif not options.no_images:
        if image_meta:  # the file is gone from Commons and the wiki: keep the old drawing
            archived.append(images.archive(t.category, t.slug, country, image_meta, options.year, options.check))
            image_meta = None
            notes.append(f"image removed from Commons, archived as valid until {options.year}")
            result.archived.append(f"`{key}`: image `{entry.file}` removed from Commons (valid until {options.year})")
            log.warning(f"{entry.code} {key}: `{entry.file}` is no longer on Commons; archived")
        elif archived:  # archived by an earlier run; nothing new to do
            log.detail(f"{entry.code} {key}: `{entry.file}` is still missing on Commons (archived)")
        else:
            result.error(f"{entry.code}: `{entry.file}` was not found on Commons or {source.wiki}")

    meta = {
        "sign": t.slug,
        "category": t.category,
        "country": country,
        "code": entry.code,
        **({"image": image_meta} if image_meta else {}),
        **({"archived": archived} if archived else {}),
        "source": {"pipeline": source.pipeline, "page": source.page_url, "file": entry.file},
    }
    names = {"en": t.name_en, source.language: entry.name}
    old_names = layout.read_translations(t.category, t.slug)

    if key not in previous:
        result.added.append(f"`{key}` ← {entry.code} {entry.name}")
        notes.insert(0, "new")
    elif old_meta != meta or any(old_names.get(lang) != name for lang, name in names.items()):
        result.changed.append(f"`{key}` ({entry.code})")
        notes.insert(0, "back on the page" if "valid_until" in old_meta else "metadata changed")
    if download:
        notes.append(f"image {download}")

    if options.check:
        _log_sign(result, label, notes)
        return
    layout.update_translations(t.category, t.slug, names)
    layout.write_json(meta_path, meta)

    if download:
        try:
            data = client.get(info["url"])
        except Exception as err:  # keep going; the report lists the failure
            result.error(f"{entry.code}: download of `{entry.file}` failed: {err}")
            return
        with open(image_path, "wb") as handle:
            handle.write(data)
        result.images.append(f"`{key}` ({download})")
        result.downloaded_bytes += len(data)
        notes[-1] = f"image downloaded, {download} ({len(data) / 1024:.1f} KB, ETA {progress.eta()})"
    notes += [f"removed old .{other} image" for other in images.remove_other_formats(t.category, t.slug, country, ext)]
    _log_sign(result, label, notes)


def _log_sign(result: Result, label: str, notes: list[str]) -> None:
    if notes:
        log.info(f"{label}: {', '.join(notes)}")
    else:
        result.unchanged += 1
        log.detail(f"{label}: up to date")


def _archive_sign(source: Source, options: Options, result: Result, key: str) -> None:
    """A sign that left the page: keep it, marked as valid until this year."""
    category, slug = key.split("/")
    meta_path = layout.sign_path(category, slug, source.country, "json")
    meta = _read_json(meta_path)
    archived = list(meta.get("archived", []))
    if meta.get("image"):
        archived.append(images.archive(category, slug, source.country, meta["image"], options.year, options.check))
    updated = {k: v for k, v in meta.items() if k not in ("image", "archived", "source")}
    updated["valid_until"] = options.year
    if archived:
        updated["archived"] = archived
    updated["source"] = meta["source"]
    if not options.check:
        layout.write_json(meta_path, updated)
    result.archived.append(f"`{key}` ({meta.get('code')}): no longer on the page (valid until {options.year})")
    log.info(f"Archived {key} ({meta.get('code')}) as valid until {options.year}")


def _delete_sign(source: Source, options: Options, result: Result, key: str) -> None:
    """--prune: delete the country's folder, and the sign when no other country has it."""
    if options.check:
        log.info(f"Would delete {key}/{source.country}")
        return
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
