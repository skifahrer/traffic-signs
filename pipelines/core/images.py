"""A sign's image file: keep it in step with Commons, archive it when it goes away.

    not on disk                      → download
    on disk, SHA-1 differs           → download the new version over it
    gone from Commons, or the sign   → rename to <sign>-<country>-archived-<year>.<ext>
    left the page                      and record it in the metadata with "valid_until"
"""

from __future__ import annotations

import os

from . import layout
from .wikimedia import sha1_of

IMAGE_EXTS = {"svg", "png", "jpg", "jpeg", "gif", "webp"}


def image_meta(path: str, info: dict) -> dict:
    """The metadata entry for the image described by Commons `info`."""
    return {
        "file": os.path.basename(path),
        "sha1": info["sha1"],
        "source": info["description_url"],
        "author": info["author"],
        "license": info["license"],
        "license_url": info["license_url"],
    }


def status(path: str, info: dict) -> str | None:
    """Why the image at `path` has to be downloaded, or None when it is current."""
    if not os.path.exists(path):
        return "missing"
    if sha1_of(path) != info["sha1"]:
        return "new version on Commons"
    return None


def archive(category: str, slug: str, country: str, meta: dict, year: int, dry_run: bool = False) -> dict:
    """Move the current image aside and return its entry for the "archived" list.

    `meta` is the image's metadata entry. The file is renamed to its archived
    name; when it was never downloaded, the entry keeps the provenance with
    "file": null.
    """
    current = os.path.join(layout.sign_dir(category, slug, country), meta["file"])
    target = None
    if os.path.exists(current):
        ext = meta["file"].rsplit(".", 1)[-1]
        target = layout.archived_path(category, slug, country, ext, year)
        if not dry_run:
            os.replace(current, target)
    return {**meta, "file": os.path.basename(target) if target else None, "valid_until": year}


def remove_other_formats(category: str, slug: str, country: str, ext: str) -> list[str]:
    """Delete a current image left over in another format (e.g. .png after a switch to .svg)."""
    removed = []
    for other in sorted(IMAGE_EXTS - {ext}):
        stale = layout.sign_path(category, slug, country, other)
        if os.path.exists(stale):
            os.remove(stale)
            removed.append(other)
    return removed
