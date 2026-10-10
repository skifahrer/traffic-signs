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
import re
import urllib.parse
from dataclasses import dataclass
from typing import Callable, Sequence, Union

from . import layout, log


@dataclass
class Entry:
    """One sign as listed on the source page."""

    file: str  # image file name without namespace, e.g. "101 Nebezpečenstvo.svg"
    code: str  # national sign code, e.g. "101", "240-3,5", "A 1a"
    name: str  # local name; "" when the page gives none (see Source.local_names)
    page: str = ""  # URL of the page it was found on, set by the sync


@dataclass
class Translation:
    """A row of translations.csv: where a national sign goes in signs/."""

    code: str
    category: str
    slug: str
    name_en: str
    name_local: str  # the local name the English one was translated from


@dataclass
class Problem:
    """A row the parser could not read as a sign."""

    file: str  # its image, so corrections.csv can still turn it into a sign
    message: str

    def __str__(self) -> str:
        return self.message


# wikitext -> (entries found, problems such as rows without a sign code)
Parser = Callable[[str], "tuple[list[Entry], list[Problem]]"]


@dataclass(frozen=True)
class Page:
    """One page the signs are read from."""

    wiki: str  # "fr.wikipedia.org"
    title: str

    @property
    def url(self) -> str:
        return f"https://{self.wiki}/wiki/" + urllib.parse.quote(self.title.replace(" ", "_"))

    @property
    def api(self) -> str:
        return f"https://{self.wiki}/w/api.php"


@dataclass(frozen=True)
class Source:
    country: str  # ISO 3166-1 alpha-2, the folder under each sign: "sk", "cz"
    language: str  # ISO 639-1 of the local names: "sk", "cs"
    country_name: str  # "Slovakia"
    language_name: str  # "Slovak"
    wiki: str  # "sk.wikipedia.org"
    # Title of the list of signs on that wiki, or several titles when the
    # signs are spread over more pages. "en:Title" reads a page from another
    # language's Wikipedia (en.wikipedia.org).
    page: Union[str, Sequence[str]]
    # One parser, or several when the page mixes layouts (e.g. galleries and
    # tables); their entries are combined. Every parser reads every page.
    parser: Union[Parser, Sequence[Parser]]
    data_dir: str  # folder with translations.csv and corrections.csv
    # Where the local names come from: "page" (the captions) or
    # "translations" (the name_<language> column of translations.csv), for
    # pages that list codes without usable names.
    local_names: str = "page"
    # Use "<name>.svg" from Commons instead of a .png/.jpg/.tif file of the
    # same name when it exists.
    prefer_svg: bool = True
    # Key of the local names in each sign's names file and in translations.csv
    # (name_<key>): the language, or the language with a region when another
    # country names signs in the same language ("de-AT"). English-speaking
    # countries use one ("en-GB", "en-US") to keep their own wording next to
    # the shared English name, which every country with the sign must agree on.
    names_key: str | None = None

    def __post_init__(self):
        if self.local_names not in ("page", "translations"):
            raise ValueError(f"{self.country}: local_names must be 'page' or 'translations', not {self.local_names!r}")

    @property
    def pages(self) -> tuple[Page, ...]:
        titles = (self.page,) if isinstance(self.page, str) else tuple(self.page)
        pages = []
        for title in titles:
            prefix, colon, rest = title.partition(":")
            if colon and re.fullmatch(r"[a-z]{2,3}", prefix):
                pages.append(Page(f"{prefix}.wikipedia.org", rest))
            else:
                pages.append(Page(self.wiki, title))
        return tuple(pages)

    @property
    def parsers(self) -> tuple[Parser, ...]:
        return tuple(self.parser) if isinstance(self.parser, (list, tuple)) else (self.parser,)

    def parse(self, wikitext: str) -> tuple[list[Entry], list[Problem]]:
        """Run every parser and combine what they find.

        A row that two parsers both read (same file and code) counts once.
        """
        entries: list[Entry] = []
        problems: list[Problem] = []
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
        """The first page: the one the country is known by in logs and reports."""
        return self.pages[0].url

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
    def name_key(self) -> str:
        return self.names_key or self.language

    @property
    def local_name_column(self) -> str:
        return f"name_{self.name_key}"

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

    def apply_corrections(self, entries: list[Entry], problems: list[Problem]) -> tuple[list[str], list[Problem]]:
        """Fix known mistakes on the page, keyed by image file.

        A correction changes the code and/or name of an entry. One that gives
        both for a row the parser could not read adds that row as a sign.
        Returns a description of each change and the problems still left.
        """
        if not os.path.exists(self.corrections_file):
            return [], problems
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
        left = []
        for problem in problems:
            fix = fixes.get(problem.file)
            if fix and fix["code"] and (fix[self.local_name_column] or self.local_names == "translations"):
                entries.append(Entry(problem.file, fix["code"], fix[self.local_name_column]))
                applied.append(f"`{problem.file}` (caption not readable) → {fix['code']} {fix[self.local_name_column]}")
            else:
                left.append(problem)
        return applied, left


def _parser_name(parser: Parser) -> str:
    return getattr(parser, "label", None) or getattr(parser, "__name__", None) or repr(parser)


def _read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if not next(iter(row.values()), "").startswith("#")]
