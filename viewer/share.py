"""Share pages: one small HTML page per sign and per category, for link previews.

Link previews (messengers, social networks, chat apps) read the page's Open
Graph tags without running JavaScript, and never see the part of a URL after
"#". So the viewer shares links to static pages,

    share/<category>/<sign>/   one sign:      title, names, countries, picture
    share/<category>/          one category:  title, number of signs, picture

each with its own title, description and image, which send a visitor on to
the viewer (#<category>/<sign>, or ?type=<category>).

Preview images must be PNG or JPEG, so they are the PNG renderings Wikimedia
Commons makes of each sign's file (most files are SVG), linked directly.
"""

from __future__ import annotations

import hashlib
import html
import os
from urllib.parse import quote, unquote

from .index import thumbnail_url

PREVIEW_WIDTH = 500  # px; Commons only renders some widths (330, 500, 960, …)
DEFAULT_SITE_URL = "https://skifahrer.github.io/traffic-signs/"


def write_share_pages(index: dict, out: str, site_url: str = DEFAULT_SITE_URL) -> int:
    """Write the share pages into `out`; returns how many were written."""
    site_url = site_url.rstrip("/") + "/"
    countries = index["countries"]
    written = 0
    by_category: dict[str, list[dict]] = {}
    for sign in index["signs"]:
        by_category.setdefault(sign["category"], []).append(sign)
        path = f"share/{sign['category']}/{sign['sign']}/"
        english = sign["names"].get("en") or sign["sign"]
        present = [countries.get(c, {}).get("name") or c.upper() for c in sign["countries"]]
        codes = ", ".join(f"{countries.get(c, {}).get('name') or c.upper()} {e.get('code') or ''}".strip() for c, e in sign["countries"].items())
        description = f"{english}, compared across {_count(len(present), 'country', 'countries')}: {codes}"
        _write(
            out,
            path,
            title=f"{english} – Traffic signs",
            description=description,
            image=preview_image(sign),
            url=site_url + _quote_path(path),
            target=f"../../../#{sign['category']}/{sign['sign']}",
        )
        written += 1
    for category, signs in by_category.items():
        label = index["categories"].get(category, category)
        path = f"share/{category}/"
        image = next((img for img in map(preview_image, signs) if img), None)
        _write(
            out,
            path,
            title=f"{label} – Traffic signs",
            description=f"{_count(len(signs), 'sign', 'signs')} compared across {_count(len(countries), 'country', 'countries')}.",
            image=image,
            url=site_url + _quote_path(path),
            target=f"../../?type={quote(category)}",
        )
        written += 1
    return written


def preview_image(sign: dict) -> str | None:
    """A PNG of the sign: the first country whose image is on Commons (or a wiki)."""
    for entry in sign["countries"].values():
        url = commons_thumbnail(entry.get("source")) or thumbnail_url(entry.get("source"), PREVIEW_WIDTH)
        if url:
            return url
    return None


def commons_thumbnail(source: str | None, width: int = PREVIEW_WIDTH) -> str | None:
    """The direct URL of the PNG that Commons renders for an SVG, PNG or JPEG file.

    https://commons.wikimedia.org/wiki/File:A.svg →
    https://upload.wikimedia.org/wikipedia/commons/thumb/<h>/<hh>/A.svg/600px-A.svg.png
    where <hh> is the start of the MD5 of the file name. Previews then need no
    redirect to reach it. Other files (TIFF, local wiki files) give None.
    """
    prefix = "https://commons.wikimedia.org/wiki/File:"
    if not source or not source.startswith(prefix):
        return None
    name = unquote(source[len(prefix) :]).replace(" ", "_")
    ext = name.rsplit(".", 1)[-1].lower()
    if ext not in ("svg", "png", "jpg", "jpeg"):
        return None
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    thumb = f"{width}px-{name}.png" if ext == "svg" else f"{width}px-{name}"
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{digest[0]}/{digest[:2]}/{quote(name)}/{quote(thumb)}"


def _write(out: str, path: str, *, title: str, description: str, image: str | None, url: str, target: str) -> None:
    e = lambda text: html.escape(text, quote=True)  # noqa: E731
    description = description if len(description) <= 300 else description[:297] + "…"
    meta = [
        f'<meta property="og:type" content="website" />',
        f'<meta property="og:site_name" content="Traffic signs" />',
        f'<meta property="og:title" content="{e(title)}" />',
        f'<meta property="og:description" content="{e(description)}" />',
        f'<meta property="og:url" content="{e(url)}" />',
        f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}" />',
        f'<meta name="twitter:title" content="{e(title)}" />',
        f'<meta name="twitter:description" content="{e(description)}" />',
    ]
    if image:
        meta += [f'<meta property="og:image" content="{e(image)}" />', f'<meta name="twitter:image" content="{e(image)}" />']
    page = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{e(title)}</title>
    <meta name="description" content="{e(description)}" />
    <link rel="canonical" href="{e(url)}" />
    {(chr(10) + '    ').join(meta)}
    <meta http-equiv="refresh" content="0; url={e(target)}" />
    <script>location.replace({_js_string(target)});</script>
  </head>
  <body>
    <p><a href="{e(target)}">{e(title)}</a></p>
  </body>
</html>
"""
    folder = os.path.join(out, *path.strip("/").split("/"))
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as handle:
        handle.write(page)


def _count(n: int, one: str, many: str) -> str:
    return f"{n:,} {one if n == 1 else many}"


def _quote_path(path: str) -> str:
    return "/".join(quote(part) for part in path.split("/"))


def _js_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("<", "\\u003c") + '"'
