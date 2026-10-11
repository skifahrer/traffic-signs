"""A sign's image file: keep it in step with Commons, archive it when it goes away.

    not on disk                      → download
    on disk, SHA-1 differs           → download the new version over it
    downloaded                       → check the bytes against Commons' SHA-1 before
                                       writing them (one retry), then write atomically
    gone from Commons, or the sign   → rename to <sign>-<country>-archived-<year>.<ext>
    left the page                      and record it in the metadata with "valid_until"
"""

from __future__ import annotations

import hashlib
import os
import time

from . import layout, log
from .wikimedia import sha1_of

IMAGE_EXTS = {"svg", "png", "jpg", "jpeg", "gif", "webp", "tif", "tiff"}
# Formats browsers display; the viewer shows the others through a Commons thumbnail.
WEB_IMAGE_EXTS = {"svg", "png", "jpg", "jpeg", "gif", "webp"}


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
    local = sha1_of(path)
    if local != info["sha1"]:
        log.detail(f"    {os.path.basename(path)}: SHA-1 on disk {local[:12]}, on Commons {info['sha1'][:12]}")
        return "new version on Commons"
    log.detail(f"    {os.path.basename(path)}: SHA-1 {local[:12]} matches Commons")
    return None


class DownloadError(Exception):
    """The image could not be fetched, or its bytes did not match Commons' SHA-1."""


DOWNLOAD_ATTEMPTS = 2  # a corrupt or truncated transfer is fetched once more


def download(client, info: dict, path: str) -> dict:
    """Fetch the image described by `info`, verify its SHA-1, and write it to `path`.

    The bytes must hash to `info["sha1"]` (what Commons reports for the file);
    a mismatch is fetched again once, then raises DownloadError and leaves the
    file on disk as it was. The file is written to a temporary name first and
    moved into place, so an interrupted run never leaves half an image.
    Returns what was downloaded: bytes, seconds, attempts, sha1.
    """
    expected = info["sha1"]
    last_error = ""
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        started = time.monotonic()
        try:
            data = client.get(info["url"])
        except Exception as err:  # noqa: BLE001 - reported with the URL below
            raise DownloadError(f"{err} ({info['url']})") from err
        seconds = time.monotonic() - started
        actual = hashlib.sha1(data).hexdigest()
        if actual == expected:
            temp = f"{path}.part"
            with open(temp, "wb") as handle:
                handle.write(data)
            os.replace(temp, path)
            log.detail(
                f"    {os.path.basename(path)}: {len(data) / 1024:.1f} KB in {seconds:.1f}s, SHA-1 {actual[:12]} verified"
                + (f" (attempt {attempt})" if attempt > 1 else "")
            )
            return {"bytes": len(data), "seconds": seconds, "attempts": attempt, "sha1": actual}
        last_error = f"SHA-1 mismatch: Commons says {expected[:12]}, the {len(data)} bytes received hash to {actual[:12]}"
        log.warning(f"{os.path.basename(path)}: {last_error} (attempt {attempt}/{DOWNLOAD_ATTEMPTS}, {info['url']})")
    raise DownloadError(last_error)


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
