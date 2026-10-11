"""Build the GitHub Pages viewer.

    python3 -m viewer                 # build into _site/
    python3 -m viewer --serve         # build, then serve on http://localhost:8000

_site/ gets the static page (viewer/static), data.json (see index.py) and a
copy of signs/ for the images.

Each build stamps its files with a version (a hash of their content):
index.html asks for `app.js?v=…` and `style.css?v=…`, and app.js for
`data.json?v=…`. A browser that cached an earlier build then fetches the new
files together, instead of running new code on old data.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import shutil

from pipelines.core import layout

from .index import build_index

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def build(out: str) -> dict:
    if os.path.isdir(out):
        shutil.rmtree(out)
    shutil.copytree(STATIC, out)
    shutil.copytree(layout.SIGNS_DIR, os.path.join(out, "signs"))
    index = build_index()
    with open(os.path.join(out, "data.json"), "w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, separators=(",", ":"))
    # data.json first, so the version of app.js covers the data it asks for.
    _stamp(out, "app.js", 'fetch("data.json")', f'fetch("data.json?v={_version(out, "data.json")}")')
    _stamp(out, "index.html", 'href="style.css"', f'href="style.css?v={_version(out, "style.css")}"')
    _stamp(out, "index.html", 'src="app.js"', f'src="app.js?v={_version(out, "app.js")}"')
    return index


def _version(out: str, name: str) -> str:
    with open(os.path.join(out, name), "rb") as handle:
        return hashlib.sha1(handle.read()).hexdigest()[:10]


def _stamp(out: str, name: str, old: str, new: str) -> None:
    path = os.path.join(out, name)
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if old not in text:
        raise RuntimeError(f"{name}: expected {old!r} to add the version to")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text.replace(old, new))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python3 -m viewer", description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=os.path.join(layout.REPO_ROOT, "_site"), help="output folder (default: _site)")
    parser.add_argument("--serve", action="store_true", help="serve the result on http://localhost:8000")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    index = build(args.out)
    print(f"Built {args.out}: {len(index['signs'])} signs, countries {', '.join(index['countries']) or 'none'}")
    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=args.out)
        print(f"Serving on http://localhost:{args.port} (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
