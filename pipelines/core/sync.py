"""The sync engine shared by every country.

    read page(s) → parse → apply corrections → match translations
      → fetch image metadata (preferring SVG) → write signs/ (names, metadata, images)
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
from .model import Entry, Page, Source, Translation
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
    download_seconds: float = 0.0
    download_failures: int = 0  # fetch failed or the SHA-1 never matched
    retried: int = 0  # downloads that matched Commons' SHA-1 only on the second try
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    archived: list[str] = field(default_factory=list)
    untranslated: list[Entry] = field(default_factory=list)
    renamed: list[str] = field(default_factory=list)
    moved: list[str] = field(default_factory=list)
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
            if source.prefer_svg:
                _prefer_svg(client, signs, info)

    previous = layout.existing_signs(source.country, source.pipeline)
    _move_signs(source, options, result, signs, previous)
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
        if result.images or result.download_failures:
            speed = result.downloaded_bytes / 1024 / result.download_seconds if result.download_seconds else 0
            log.info(
                f"Downloads: {len(result.images)} verified against Commons' SHA-1"
                f" ({result.retried} after a retry), {result.download_failures} failed;"
                f" {result.download_seconds:.0f}s fetching, {speed:.0f} KB/s"
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
    """Parse the page(s) and pair every entry with its translation."""
    entries: list[Entry] = []
    problems = []
    seen: set[tuple[str, str]] = set()
    for page, wikitext in _read_pages(source, client, options):
        found, found_problems = source.parse(wikitext)
        if len(source.pages) > 1:
            log.info(f"{page.title}: {len(found)} entries, {len(found_problems)} problems")
        for entry in found:
            entry.page = page.url
            # A sign listed on two pages (an overview and its own page) counts once.
            if (entry.file, entry.code) not in seen:
                seen.add((entry.file, entry.code))
                entries.append(entry)
        problems += found_problems

    changes, problems = source.apply_corrections(entries, problems)
    for change in changes:
        log.info(f"Correction applied: {change}")
    log.info(f"{len(entries)} entries with a sign code")
    for problem in problems:
        result.error(str(problem))

    translations, problems = source.load_translations()
    log.info(f"{len(translations)} translations in {os.path.relpath(source.translations_file, layout.REPO_ROOT)}")
    for problem in problems:
        result.error(problem)

    by_code: dict[str, Entry] = {}
    for entry in entries:
        first = by_code.get(entry.code)
        if first and first.page and entry.page and first.page != entry.page:
            # The same sign on a later page with another image (a variant, an older
            # drawing): the page listed first, usually the local one, has the say.
            log.detail(f"{entry.code}: `{entry.file}` from {entry.page} skipped, `{first.file}` from {first.page} is used")
            continue
        if first:
            result.error(
                f"code {entry.code} appears twice: `{by_code[entry.code].file}` and `{entry.file}`"
                " (add a line to corrections.csv)"
            )
            continue
        by_code[entry.code] = entry

    signs = [(entry, translations[code]) for code, entry in by_code.items() if code in translations]
    if source.local_names == "translations":
        for entry, t in signs:
            entry.name = t.name_local
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


def _read_pages(source: Source, client: Client, options: Options) -> list[tuple[Page, str]]:
    """The wikitext of every page; --wikitext stands in for all of them."""
    if options.wikitext:
        log.info(f"Reading {options.wikitext}")
        with open(options.wikitext, encoding="utf-8") as handle:
            wikitext = handle.read()
        log.info(f"{len(wikitext):,} characters of wikitext")
        return [(source.pages[0], wikitext)]
    pages = []
    for page in source.pages:
        log.info(f"Downloading {page.url}")
        wikitext = client.page_wikitext(page.wiki, page.title)
        log.info(f"{len(wikitext):,} characters of wikitext")
        pages.append((page, wikitext))
    return pages


def _fetch_image_info(source: Source, client: Client, files: list[str]) -> dict[str, dict]:
    """imageinfo per file name, looking on Commons first, then on the pages' wikis."""
    titles = [f"File:{f}" for f in files]
    info = client.image_info(COMMONS_API, titles)
    log.info(f"Found {len(info)}/{len(titles)} files on Commons")
    for page in {p.wiki: p for p in source.pages}.values():
        missing = [t for t in titles if t not in info]
        if not missing:
            break
        local = client.image_info(page.api, missing)
        log.info(f"Found {len(local)}/{len(missing)} of the rest on {page.wiki}")
        info.update(local)
    return {title[len("File:"):]: value for title, value in info.items()}


def _prefer_svg(client: Client, signs: list[tuple[Entry, Translation]], info: dict[str, dict]) -> None:
    """Swap a .png/.jpg/.tif image for "<same name>.svg" when Commons has it."""
    raster = [entry for entry, _ in signs if not entry.file.lower().endswith(".svg")]
    if not raster:
        return
    svg_name = {entry.file: entry.file.rsplit(".", 1)[0] + ".svg" for entry in raster}
    found = client.image_info(COMMONS_API, [f"File:{name}" for name in sorted(set(svg_name.values()))])
    swapped = 0
    for entry in raster:
        svg = found.get(f"File:{svg_name[entry.file]}")
        if svg:
            log.detail(f"{entry.code}: using `{svg_name[entry.file]}` instead of `{entry.file}`")
            entry.file = svg_name[entry.file]
            info[entry.file] = svg
            swapped += 1
    log.info(f"{swapped}/{len(raster)} non-SVG images have an SVG version on Commons; using it")


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
    if info is None and old_meta.get("source", {}).get("file") == entry.file.rsplit(".", 1)[0] + ".svg":
        # --no-images does not look for SVG versions (_prefer_svg); keep the one found before.
        entry.file = old_meta["source"]["file"]
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
            result.error(f"{entry.code}: `{entry.file}` was not found on Commons or {', '.join(sorted({p.wiki for p in source.pages}))}")

    meta = {
        "sign": t.slug,
        "category": t.category,
        "country": country,
        "code": entry.code,
        **({"image": image_meta} if image_meta else {}),
        **({"archived": archived} if archived else {}),
        "source": {"pipeline": source.pipeline, "page": entry.page or source.page_url, "file": entry.file},
    }
    names = {"en": t.name_en, source.name_key: entry.name}
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
        log.detail(f"    downloading `{entry.file}` ({download}) from {info['url']}")
        try:
            got = images.download(client, info, image_path)
        except images.DownloadError as err:  # keep going; the report lists the failure
            result.download_failures += 1
            result.error(f"{entry.code}: download of `{entry.file}` failed: {err}")
            return
        result.images.append(f"`{key}` ({download})")
        result.downloaded_bytes += got["bytes"]
        result.download_seconds += got["seconds"]
        result.retried += got["attempts"] > 1
        notes[-1] = (
            f"image downloaded, {download} ({got['bytes'] / 1024:.1f} KB in {got['seconds']:.1f}s,"
            f" SHA-1 verified{', after a retry' if got['attempts'] > 1 else ''}, ETA {progress.eta()})"
        )
    if info is not None:  # with --no-images the image on disk was not checked, so it stays
        notes += [f"removed old .{other} image" for other in images.remove_other_formats(t.category, t.slug, country, ext)]
    _log_sign(result, label, notes)


def _log_sign(result: Result, label: str, notes: list[str]) -> None:
    if notes:
        log.info(f"{label}: {', '.join(notes)}")
    else:
        result.unchanged += 1
        log.detail(f"{label}: up to date")


def _move_signs(
    source: Source, options: Options, result: Result, signs: list[tuple[Entry, Translation]], previous: dict[str, str]
) -> None:
    """Signs whose translation now names another folder: move them there, with their images and archive.

    A sign moves when translations.csv gives its code a new category or slug
    (merging it into a sign other countries have, say). Moving keeps its
    images and history, where a new folder plus an archived old one would
    show it twice. `previous` is updated to the new places.
    """
    wanted = {f"{t.category}/{t.slug}" for _, t in signs}
    left = {(_read_json(path) or {}).get("code"): key for key, path in previous.items() if key not in wanted}
    for entry, t in signs:
        new = f"{t.category}/{t.slug}"
        old = left.get(entry.code)
        if new in previous or not old:
            continue
        result.moved.append(f"`{old}` → `{new}` ({entry.code})")
        log.info(f"{entry.code}: moved from {old} to {new}" + (" (check only)" if options.check else ""))
        if not options.check:
            _move_sign(source, old, new)
        previous[new] = layout.sign_path(t.category, t.slug, source.country, "json") if not options.check else previous[old]
        del previous[old]


def _move_sign(source: Source, old: str, new: str) -> None:
    country = source.country
    (old_category, old_slug), (category, slug) = old.split("/"), new.split("/")
    old_dir, new_dir = layout.sign_dir(old_category, old_slug, country), layout.sign_dir(category, slug, country)
    if os.path.exists(new_dir):
        raise RuntimeError(f"cannot move {old}/{country}: {new}/{country} already exists")
    os.makedirs(new_dir)
    renamed = lambda name: name.replace(f"{old_slug}-{country}", f"{slug}-{country}", 1)  # noqa: E731
    for name in os.listdir(old_dir):
        shutil.move(os.path.join(old_dir, name), os.path.join(new_dir, renamed(name)))
    meta_path = layout.sign_path(category, slug, country, "json")
    meta = _read_json(meta_path)
    meta.update(sign=slug, category=category)
    for image in [meta.get("image"), *meta.get("archived", [])]:
        if image:
            image["file"] = renamed(image["file"])
    layout.write_json(meta_path, meta)
    names = layout.read_translations(old_category, old_slug)
    if source.name_key in names:
        layout.update_translations(category, slug, {source.name_key: names[source.name_key]})
    _remove_dir(old_dir)
    if layout.country_dirs(old_category, old_slug):
        layout.remove_translation(old_category, old_slug, source.name_key)
    elif os.path.isdir(os.path.dirname(layout.translations_path(old_category, old_slug))):
        _remove_dir(os.path.dirname(layout.translations_path(old_category, old_slug)))


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
        layout.remove_translation(category, slug, source.name_key)
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
