"""Sync traffic signs from Wikipedia into signs/.

    python -m pipelines                  # every country
    python -m pipelines sk cz            # only these countries
    python -m pipelines --list           # show the available countries
    python -m pipelines sk --check -v    # report what would change, log every sign
"""

from __future__ import annotations

import argparse
import sys

from .core import layout, log, report
from .core.sync import Options, Result, sync
from .core.wikimedia import Client
from .countries import all_sources


def main(argv: list[str] | None = None) -> int:
    sources = all_sources()
    parser = argparse.ArgumentParser(
        prog="python -m pipelines", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "countries", nargs="*", metavar="country", help=f"country codes or `all` (default); available: {', '.join(sources)}"
    )
    parser.add_argument("--list", action="store_true", help="list the available countries and exit")
    parser.add_argument("--check", action="store_true", help="report changes without writing anything")
    parser.add_argument("--no-images", action="store_true", help="skip Commons metadata and image downloads")
    parser.add_argument("--prune", action="store_true", help="delete signs that are no longer on the page")
    parser.add_argument("--strict", action="store_true", help="fail when a sign has no translation")
    parser.add_argument("--wikitext", help="read the page from this file instead of downloading it (one country only)")
    parser.add_argument("--report", help="also write the Markdown report to this file")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between Wikimedia requests")
    parser.add_argument("-v", "--verbose", action="store_true", help="also log signs that are already up to date")
    args = parser.parse_args(argv)

    if args.list:
        for code, source in sources.items():
            print(f"{code}  {source.country_name:<16} {source.page_url}")
        return 0

    requested = [c.lower() for c in args.countries if c.lower() != "all"] or list(sources)
    unknown = [c for c in requested if c not in sources]
    if unknown:
        parser.error(f"unknown country {', '.join(unknown)}; available: {', '.join(sources)}")
    if args.wikitext and len(requested) != 1:
        parser.error("--wikitext needs exactly one country")

    log.verbose = args.verbose
    log.info(f"Syncing {', '.join(requested)}")
    options = Options(
        check=args.check, no_images=args.no_images, prune=args.prune, strict=args.strict, wikitext=args.wikitext
    )
    client = Client(delay=args.delay)
    results = []
    for code in requested:
        try:
            results.append(sync(sources[code], client, options))
        except Exception as err:  # one broken country must not stop the others
            result = Result(sources[code], options)
            result.error(f"sync stopped: {err!r}")
            results.append(result)

    text = report.render(results)
    print(text)
    if args.report:
        layout.write_text(args.report, text)
        log.info(f"Report written to {args.report}")

    failed = [r.source.country for r in results if r.failed]
    images = sum(len(r.images) for r in results)
    errors = sum(len(r.errors) for r in results)
    log.info(
        f"{'Failed (' + ', '.join(failed) + ')' if failed else 'Finished'} in {log.duration(log.elapsed())}:"
        f" {sum(r.synced for r in results)} signs, {images} images downloaded, {errors} errors"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
