"""Build the GitHub Pages viewer.

    python3 -m viewer                 # build into _site/
    python3 -m viewer --serve         # build, then serve on http://localhost:8000

_site/ gets the static page (viewer/static), data.json (see index.py) and a
copy of signs/ for the images.
"""

from __future__ import annotations

import argparse
import functools
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
    return index


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
