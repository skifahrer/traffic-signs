"""Which signs OpenStreetMap supports, and which image in signs/ draws each.

OSM has no catalogue of sign codes: `traffic_sign` holds `<CC>:<national code>`
(`SK:253[50]`, `DE:274[50],1020-30`) or one of the human-readable values the
wiki documents (`city_limit`, `stop`, ...). So "supported" is read from OSM
itself:

    coded values     every `<CC>:` value mappers have tagged, from taginfo
                     (keys traffic_sign, traffic_sign:forward, traffic_sign:backward)
    human values     the values Key:traffic_sign documents, from the OSM wiki
    implied signs    highway=stop|give_way|traffic_signals|speed_camera

Each value is matched to a sign of that country by its code, through
aliases.csv where OSM still uses a code the country has since renumbered
(Slovakia's 2009 `P1` is today's `201`). The result is one file per country:

    osm/<cc>.json   {"signs": {value: {"sign": "<category>/<slug>", "count": n}},
                     "unmatched": {value: count}, ...}

`unmatched` is what to fix next: an alias, or a sign the collection lacks.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, field

from ..core import layout

OSM_DIR = os.path.join(layout.REPO_ROOT, "osm")
ALIASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aliases.csv")
TAGINFO = "https://taginfo.openstreetmap.org/api/4/key/values"
WIKI_API = "https://wiki.openstreetmap.org/w/api.php"
KEYS = ("traffic_sign", "traffic_sign:forward", "traffic_sign:backward")

# human-readable values the wiki documents → the sign that shows them
HUMAN = {
    "city_limit": "information/built-up-area",
    "city_limit_end": "information/end-of-built-up-area",
    "give_way": "regulatory/give-way",
    "stop": "regulatory/stop",
    "hazard": "warning/danger",
    "maxheight": "regulatory/maximum-height",
    "maxweight": "regulatory/maximum-weight",
    "maxwidth": "regulatory/maximum-width",
    "overtaking": "regulatory/no-overtaking",
    "overtaking_end": "regulatory/end-of-no-overtaking",
    "signal_ahead": "warning/traffic-signals",
    "stop_ahead": "warning/stop-ahead",
    "yield_ahead": "warning/give-way-ahead",
}
# these take their figure from the tag of the same name: one sign per figure
FIGURES = {
    "maxspeed": re.compile(r"^regulatory/speed-limit-(\d+)$"),
    "maxweight": re.compile(r"^regulatory/maximum-weight-(\d+(?:-\d+)?)t$"),
    "maxheight": re.compile(r"^regulatory/maximum-height-(\d+(?:-\d+)?)m$"),
    "maxwidth": re.compile(r"^regulatory/maximum-width-(\d+(?:-\d+)?)m$"),
}
# nodes that are a sign without `traffic_sign`
IMPLIED = {
    "stop": "regulatory/stop",
    "give_way": "regulatory/give-way",
    "traffic_signals": "warning/traffic-signals",
    "speed_camera": "information/speed-camera",
}
PREFIX = re.compile(r"^([A-Z]{2}):(.*)$")
VALUE = re.compile(r"^(.*?)\[(.*)\]$")


def code(text: str) -> str:
    """A national code as maps spell it: `P 6`, `§52 Z24` and `3,5` lose spaces, `§` and commas."""
    return re.sub(r"[\s§]", "", text).replace(",", "-").lower()


# where OSM and the national list write one code two ways
SPELLING = {
    "at": lambda c: re.sub(r"^(\d+)\.", r"\1z", c),  # `52.10a` is `§52 Z10a`
    "hu": lambda c: re.sub(r"^([a-z])-?0*(\d+)", lambda m: f"{m.group(1)}-{int(m.group(2)):03d}", c),
}


def spelled(country: str, text: str) -> str:
    """`code`, then the country's own spelling, so both sides of a match read alike."""
    return SPELLING.get(country, lambda c: c)(code(text))


def components(value: str) -> list[str]:
    """Signs of one tag value: `;` parts, then `,` panels outside brackets, each with its country."""
    out = []
    for part in value.split(";"):
        country, depth, start = "", 0, 0
        pieces = []
        for i, ch in enumerate(part + ","):
            depth += (ch == "[") - (ch == "]")
            if ch == "," and depth <= 0:
                pieces.append(part[start:i].strip())
                start = i + 1
        for piece in filter(None, pieces):
            m = PREFIX.match(piece)
            if m:
                country = m.group(1)
            elif country and not piece.islower():
                piece = f"{country}:{piece}"
            out.append(piece)
    return out


@dataclass
class Collection:
    """The signs of one country in signs/, by code and by folder."""

    country: str
    by_code: dict[str, str] = field(default_factory=dict)
    folders: set[str] = field(default_factory=set)

    @classmethod
    def read(cls, country: str, root: str | None = None) -> "Collection":
        root = root or layout.SIGNS_DIR
        found = cls(country)
        for category in sorted(os.listdir(root)) if os.path.isdir(root) else []:
            for slug in sorted(os.listdir(os.path.join(root, category))):
                meta = os.path.join(root, category, slug, country, f"{slug}-{country}.json")
                if not os.path.isfile(meta):
                    continue
                with open(meta, encoding="utf-8") as f:
                    data = json.load(f)
                path = f"{category}/{slug}"
                found.folders.add(path)
                if data.get("code"):
                    found.by_code.setdefault(spelled(country, data["code"]), path)
        return found


def read_aliases(path: str = ALIASES) -> dict[tuple[str, str], str]:
    """`{(country, osm code): code in signs/}` from aliases.csv."""
    with open(path, encoding="utf-8", newline="") as f:
        return {(row["country"].lower(), spelled(row["country"].lower(), row["osm"])):
            spelled(row["country"].lower(), row["code"])
                for row in csv.DictReader(f) if not row["country"].startswith("#")}


def match(value: str, signs: Collection, aliases: dict[tuple[str, str], str],
          human: set[str]) -> str | None:
    """The sign that draws one component, `SK:253[50]` or `city_limit`; None when none does."""
    m = PREFIX.match(value)
    if not m:
        if value in human and HUMAN.get(value) in signs.folders:
            return HUMAN[value]
        return None
    if m.group(1).lower() != signs.country:
        return None
    body = m.group(2)
    v = VALUE.match(body)
    base, figure = (v.group(1), v.group(2)) if v else (body, "")
    key = spelled(signs.country, base)
    key = aliases.get((signs.country, key), key)
    wanted = f"{key}-{code(figure)}" if figure.strip() else key
    return signs.by_code.get(wanted)


def figures(signs: Collection) -> dict[str, dict[str, str]]:
    """`{"maxspeed": {"50": "regulatory/speed-limit-50"}, "maxweight": {"7-5": ...}}`."""
    out: dict[str, dict[str, str]] = {}
    for value, pattern in FIGURES.items():
        for path in sorted(signs.folders):
            m = pattern.match(path)
            if m:
                out.setdefault(value, {})[m.group(1)] = path
    return out


def summarise(country: str, coded: dict[str, int], human: dict[str, int], signs: Collection,
              aliases: dict[tuple[str, str], str], meta: dict) -> dict:
    """The country's file: what OSM supports and has an image, and what it lacks."""
    matched, unmatched = {}, {}
    for value, count in sorted(coded.items(), key=lambda kv: (-kv[1], kv[0])):
        sign = match(value, signs, aliases, set())
        if sign:
            matched[value] = {"sign": sign, "count": count}
        else:
            unmatched[value] = count
    documented = {v: {"sign": HUMAN[v], "count": human.get(v, 0)}
                  for v in sorted(human) if HUMAN.get(v) in signs.folders}
    return {
        "country": country,
        **meta,
        "signs": {**documented, **matched},
        "figures": figures(signs),
        "implied": {k: v for k, v in IMPLIED.items() if v in signs.folders},
        "unmatched": unmatched,
        "human_without_image": sorted(v for v in human if v not in documented and v not in FIGURES),
    }


def taginfo_values(client, country: str) -> tuple[dict[str, int], str]:
    """`{component: uses}` of the country's coded values over every sign key, and the data date."""
    used: dict[str, int] = {}
    until = ""
    for key in KEYS:
        page = 1
        while True:
            data = json.loads(client.get(TAGINFO, {
                "key": key, "query": f"{country.upper()}:", "filter": "all", "rp": 999, "page": page,
                "sortname": "count", "sortorder": "desc"}))
            until = data.get("data_until") or until
            for row in data.get("data") or []:
                for piece in components(row["value"]):
                    if piece.startswith(f"{country.upper()}:"):
                        used[piece] = used.get(piece, 0) + int(row["count"])
            if page * 999 >= int(data.get("total") or 0):
                break
            page += 1
    return used, until


def human_values(client) -> set[str]:
    """Human-readable values Key:traffic_sign documents, with the wiki's own variants."""
    data = json.loads(client.get(WIKI_API, {"action": "parse", "page": "Key:traffic_sign",
                                            "prop": "wikitext", "format": "json"}))
    text = data["parse"]["wikitext"]["*"]
    found = set(re.findall(r"\{\{[Tt]ag\|traffic_sign\|([a-z_]+)\}\}", text))
    # the wiki tags the end signs as `city_limit=end` and `overtaking=yes`
    found |= {f"{v}_end" for v in ("city_limit", "overtaking") if v in found}
    return found


def human_uses(client) -> dict[str, int]:
    """Uses of the human-readable values worldwide; they carry no country."""
    used: dict[str, int] = {}
    for key in KEYS:
        data = json.loads(client.get(TAGINFO, {"key": key, "filter": "all", "rp": 999, "page": 1,
                                               "sortname": "count", "sortorder": "desc"}))
        for row in data.get("data") or []:
            for piece in components(row["value"]):
                if not PREFIX.match(piece):
                    used[piece] = used.get(piece, 0) + int(row["count"])
    return used
