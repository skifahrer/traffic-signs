"""What a country pipeline is made of.

A country is described by one `Source`: where its list of signs lives on
Wikipedia, how to read that page (one or more parsers: from `parsers.py`, or
any function of its own), and a folder with two CSV files:

    translations.csv   code,category,slug,name_en,name_<lang>
    corrections.csv    file,code,name_<lang>,note

Everything else (downloading, matching, writing signs/, reporting) is shared
and lives in `sync.py`.
"""

from __future__ import annotations

import csv
import os
import urllib.parse
from dataclasses import dataclass
from typing import Callable, Sequence, Union

from . import layout, log


@dataclass
class Entry:
    """One sign as listed on the source page."""

    file: str  # image file name without namespace, e.g. "101 Nebezpečenstvo.svg"
    code: str  # national sign code, e.g. "101", "240-3,5", "A 1a"
    name: str  # local name


@dataclass
class Translation:
    """A row of translations.csv: where a national sign goes in signs/."""

    code: str
    category: str
    slug: str
    name_en: str
    name_local: str  # the local name the English one was translated from


# wikitext -> (entries found, problems such as rows without a sign code)
Parser = Callable[[str], "tuple[list[Entry], list[str]]"]


@dataclass(frozen=True)
class Source:
    country: str  # ISO 3166-1 alpha-2, the folder under each sign: "sk", "cz"
    language: str  # ISO 639-1 of the local names: "sk", "cs"
    country_name: str  # "Slovakia"
    language_name: str  # "Slovak"
    wiki: str  # "sk.wikipedia.org"
    page: str  # title of the list of signs on that wiki
    # One parser, or several when the page mixes layouts (e.g. galleries and
    # tables); their entries are combined.
    parser: Union[Parser, Sequence[Parser]]
    data_dir: str  # folder with translations.csv and corrections.csv

    @property
    def parsers(self) -> tuple[Parser, ...]:
        return tuple(self.parser) if isinstance(self.parser, (list, tuple)) else (self.parser,)

    def parse(self, wikitext: str) -> tuple[list[Entry], list[str]]:
        """Run every parser and combine what they find.

        A row that two parsers both read (same file and code) counts once.
        """
        entries: list[Entry] = []
        problems: list[str] = []
        seen: set[tuple[str, str]] = set()
        for parser in self.parsers:
            found, found_problems = parser(wikitext)
            if len(self.parsers) > 1:
                log.info(f"{_parser_name(parser)}: {len(found)} entries, {len(found_problems)} problems")
            for entry in found:
                if (entry.file, entry.code) not in seen:
                    seen.add((entry.file, entry.code))
                    entries.append(entry)
            problems += found_problems
        return entries, problems

    @property
    def pipeline(self) -> str:
        """Written into each sign's metadata, so a sync only touches its own signs."""
        return f"{self.country}-wikipedia"

    @property
    def page_url(self) -> str:
        return f"https://{self.wiki}/wiki/" + urllib.parse.quote(self.page.replace(" ", "_"))

    @property
    def api(self) -> str:
        return f"https://{self.wiki}/w/api.php"

    @property
    def translations_file(self) -> str:
        return os.path.join(self.data_dir, "translations.csv")

    @property
    def corrections_file(self) -> str:
        return os.path.join(self.data_dir, "corrections.csv")

    @property
    def local_name_column(self) -> str:
        return f"name_{self.language}"

    def load_translations(self) -> tuple[dict[str, Translation], list[str]]:
        """Translations keyed by sign code, and any problems found in the file."""
        translations: dict[str, Translation] = {}
        problems: list[str] = []
        seen: dict[str, str] = {}
        for row in _read_csv(self.translations_file):
            t = Translation(row["code"], row["category"], row["slug"], row["name_en"], row[self.local_name_column])
            try:
                layout.validate(t.category, t.slug, self.country)
            except ValueError as err:
                problems.append(f"translations.csv, code {t.code}: {err}")
                continue
            key = f"{t.category}/{t.slug}"
            if t.code in translations:
                problems.append(f"translations.csv lists code {t.code} twice")
            if key in seen:
                problems.append(f"translations.csv maps codes {seen[key]} and {t.code} to the same sign `{key}`")
            seen[key] = t.code
            translations[t.code] = t
        return translations, problems

    def apply_corrections(self, entries: list[Entry]) -> list[str]:
        """Fix known mistakes on the page; returns a description of each change."""
        if not os.path.exists(self.corrections_file):
            return []
        fixes = {row["file"]: row for row in _read_csv(self.corrections_file)}
        applied = []
        for entry in entries:
            fix = fixes.get(entry.file)
            if not fix:
                continue
            code, name = fix["code"] or entry.code, fix[self.local_name_column] or entry.name
            if (code, name) != (entry.code, entry.name):
                applied.append(f"{entry.code} {entry.name} → {code} {name}")
            entry.code, entry.name = code, name
        return applied


def _parser_name(parser: Parser) -> str:
    return getattr(parser, "label", None) or getattr(parser, "__name__", None) or repr(parser)


def _read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if not next(iter(row.values()), "").startswith("#")]
