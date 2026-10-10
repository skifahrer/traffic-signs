# Traffic signs

An open collection of road traffic signs from around the world, organised by
what a sign means rather than by country. The same sign from different
countries sits side by side, so you can compare Slovakia's "steep descent" with
Czechia's or Germany's.

## Layout

```
signs/
  <category>/                 warning, regulatory, information, ...
    <sign>/                   English name of the concrete sign, e.g. bend-left
      <sign>.json             the sign's names, one entry per language
      <country>/              ISO 3166-1 alpha-2 code, lowercase: sk, cz, us, ...
        <sign>-<country>.svg  the image (svg, png, ...)
        <sign>-<country>.json metadata: national code, image source and licence
```

For example:

```
signs/warning/danger/
  danger.json        {"en": "Other danger", "sk": "Nebezpečenstvo"}
  sk/
    danger-sk.svg    the sign
    danger-sk.json   {"code": "101", "image": {...}, "source": {...}}
```

The names file is shared by every country that has the sign. Keys are
ISO 639-1 language codes, `en` first; when a country is added, its language is
added to the same file, e.g. `"cs": "Jiné nebezpečí"` for Czechia. If two
countries name a sign differently in the same language, add a region to the
key for the second one, e.g. `de` for Germany and `de-AT` for Austria.

### Categories

| Folder | Contains |
| --- | --- |
| `warning` | Warning signs |
| `regulatory` | Priority, prohibitory, mandatory and parking signs |
| `information` | Information, direction and lane signs |
| `additional-panel` | Panels placed below another sign (distance, direction, ...) |
| `traffic-device` | Barriers, direction boards, cones and other guiding devices |
| `traffic-signal` | Traffic lights and their supplementary devices |

### Naming signs

Sign folders are English, lowercase, with words separated by hyphens:
`bend-left`, `no-entry`, `speed-limit-50`. A variant of a sign (direction,
value, placement) is its own sign: `steep-descent-10-percent`,
`maximum-weight-3-5t` (decimal comma becomes a hyphen), `pedestrians-left-side`
(the mirrored version for placing on the left side of the road).

When you add a country, reuse an existing folder if the sign has the same
meaning, so the countries line up.

## Countries

| Country | Signs | Source | Pipeline |
| --- | --- | --- | --- |
| Slovakia (`sk`) | 837 | [Zoznam dopravných značiek na Slovensku](https://sk.wikipedia.org/wiki/Zoznam_dopravn%C3%BDch_zna%C4%8Diek_na_Slovensku) (Slovak Wikipedia, VL 6.1 / 6.3 / 6.4) | [`pipelines/countries/sk`](pipelines/countries/sk) |

## Pipelines

Each country's signs come from a list on Wikipedia. One command syncs every
country, or the ones you name:

```sh
python3 -m pipelines                  # every country
python3 -m pipelines sk               # only Slovakia (several: sk cz pl)
python3 -m pipelines --list           # available countries
python3 -m pipelines sk --no-images   # names and metadata only
python3 -m pipelines sk --check       # report what would change, write nothing
python3 -m pipelines sk --prune       # also delete signs removed from the page
python3 -m pipelines sk -v            # also log signs that are already up to date
```

For every sign on the page it merges the English and local names into the
sign's names file (other languages are kept), writes the country's metadata,
and downloads the image from Wikimedia Commons when its SHA-1 differs from the
file on disk, so a re-run is cheap. One country failing does not stop the
others; the exit code is non-zero if any of them failed.

Progress goes to stderr with timestamps: each phase, every sign it creates,
changes or downloads an image for (`[123/837] 253-50 → regulatory/speed-limit-50`),
retries with their HTTP status, an ETA while downloading, and a summary at the
end. The Markdown report goes to stdout. On GitHub Actions the phases are
collapsible groups and errors are shown as annotations.

It needs Python 3.9+ and nothing else.

### Code layout

```
pipelines/
  __main__.py          command line: picks the countries, runs them, writes the report
  core/                shared by every country
    model.py           Source (a country's settings), Entry, Translation
    parsers.py         reusable page readers: gallery(), wikitable()
    sync.py            the sync engine: page → translations → images → signs/
    report.py          Markdown report for the job summary and the pull request
    layout.py          the signs/ folder structure
    wikimedia.py       HTTP client with User-Agent, rate limit and retries
    log.py             progress logging
  countries/
    sk/
      __init__.py      SOURCE = Source(...) for Slovakia
      translations.csv code → category, English folder name, English and Slovak name
      corrections.csv  fixes for mistakes on the Wikipedia page
```

### Adding a country

1. Create `pipelines/countries/<code>/` (ISO 3166-1 alpha-2, e.g. `cz`, `pl`)
   with an `__init__.py` that defines `SOURCE`. Pick the parser that matches the
   page: `parsers.gallery(...)` for `<gallery>` lists, `parsers.wikitable(...)`
   for tables with an image cell followed by a "code name" cell. For example:

   ```python
   SOURCE = Source(
       country="cz",
       language="cs",
       country_name="Czechia",
       language_name="Czech",
       wiki="cs.wikipedia.org",
       page="Seznam dopravních značek v Česku",
       parser=parsers.wikitable(r"[A-Z]{1,2} \d+[a-z]?", namespaces=("Soubor",)),
       data_dir=os.path.dirname(os.path.abspath(__file__)),
   )
   ```

   The code pattern decides which rows count as signs; every row it does not
   match is reported as an error, so tune it (or add corrections) until
   `--check` is clean.

   `parser` also takes a list, for a page that mixes layouts. The entries
   found by all of them are combined, and a row two parsers both read counts
   once:

   ```python
   parser=[
       parsers.gallery(r"\d{3}", namespaces=("Plik",)),
       parsers.wikitable(r"[A-Z]-\d+[a-z]?", namespaces=("Plik",)),
       parse_bullet_list,  # countries/pl/parser.py: a function of its own
   ],
   ```

   A parser is any function that takes the page's wikitext and returns
   `(entries, problems)`. Write one in the country's own package when only
   that page is laid out that way, or add a factory to `core/parsers.py` when
   other countries can reuse it.
2. Add `translations.csv` with the columns `code,category,slug,name_en,name_<language>`.
   Reuse an existing sign folder (`slug`) when the sign means the same, so the
   countries line up. Run `python3 -m pipelines <code> --check` to see which
   codes on the page still need a row.
3. Optionally add `corrections.csv` (`file,code,name_<language>,note`).

The command line and the sync workflow find the new country automatically.

### Automatic updates

[`.github/workflows/sync.yml`](.github/workflows/sync.yml) syncs every country
each Monday. From the Actions tab, *Sync signs from Wikipedia → Run workflow*
takes `all` or a list of country codes, plus the prune and verbose switches. It
opens (or updates) a pull request on `sync/<countries>` with the changes and a
report listing new, changed, removed and untranslated signs. For it to open
pull requests, enable *Settings → Actions → General → Allow GitHub Actions to
create and approve pull requests*.

## Licence

The repository's own content (structure, names, metadata, code) is
[CC0 1.0](LICENSE). Images keep the licence of their source, recorded in each
sign's `.json` under `image.license`. The Slovak sign drawings on Wikimedia
Commons are official works of the Slovak government and in the public domain
(`PD-SlovakGov`).
