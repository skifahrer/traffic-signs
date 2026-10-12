"""Write osm/<cc>.json: the signs OSM supports per country, and their images.

    python -m pipelines.osm              # every country in signs/
    python -m pipelines.osm sk cz        # only these
    python -m pipelines.osm sk --check   # print the summary, write nothing
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from ..core import layout, log
from ..core.wikimedia import Client
from ..countries import all_sources
from . import (OSM_DIR, Collection, human_uses, human_values, read_aliases, summarise,
               taginfo_values)


def countries() -> list[str]:
    """Countries with signs of their own; regions such as `us-ca` share their country's OSM prefix."""
    return sorted({code.split("-")[0] for code in all_sources()})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipelines.osm", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("countries", nargs="*", metavar="country")
    parser.add_argument("--check", action="store_true", help="report without writing")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    args = parser.parse_args(argv)
    chosen = [c.lower() for c in args.countries] or countries()

    client = Client(delay=args.delay)
    human = human_values(client)
    log.info(f"OSM wiki documents {len(human)} human-readable values: {', '.join(sorted(human))}")
    uses = human_uses(client)
    worldwide = {v: uses.get(v, 0) for v in human}
    aliases = read_aliases()
    failed = False
    for country in chosen:
        try:
            coded, until = taginfo_values(client, country)
        except Exception as err:  # one country must not stop the others
            log.error(f"{country}: taginfo failed: {err!r}")
            failed = True
            continue
        meta = {"taginfo": {"data_until": until, "url": "https://taginfo.openstreetmap.org/keys/traffic_sign"},
                "note": "counts of human-readable values are worldwide; coded ones are this country's"}
        result = summarise(country, coded, worldwide, Collection.read(country), aliases, meta)
        drawn = sum(v["count"] for k, v in result["signs"].items() if k in coded)
        missing = sum(result["unmatched"].values())
        log.info(f"{country}: {len(coded)} coded values in OSM; {len(coded) - len(result['unmatched'])} "
                 f"with an image ({drawn} uses), {len(result['unmatched'])} without ({missing} uses)")
        if not args.check:
            os.makedirs(OSM_DIR, exist_ok=True)
            layout.write_text(os.path.join(OSM_DIR, f"{country}.json"),
                              json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
