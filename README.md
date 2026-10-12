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
        <sign>-<country>-archived-<year>.svg   an earlier image, valid until <year>
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
English-speaking countries keep their own wording under such a key next to the
shared `en`: `{"en": "Give way", "en-GB": "Give way", "en-US": "Yield"}`.

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

The viewer relies on this naming to tie variants to their sign: a folder whose
name is another folder's name plus a side (`-left`, `-from-right`,
`-left-side`), a value (`-50`, `-3-5t`, `-20mph`, `-10-percent`) or a design
letter (`-b`) is shown as that sign's variant. Variants are not blended into
their sign: each keeps its own row, and a row compares only countries with
that very sign, so Germany with only `crosswind-from-left` and
`crosswind-from-right` is not shown in the `crosswind` row. The sign's
detail links to its variants and back.

## Viewer

**<https://skifahrer.github.io/traffic-signs/>** shows every sign with one
column per country, so the same sign can be compared across countries. Filter
by type (a button per type, each with how many signs the other filters leave
in it), by country (*All* and *None* next to the country chips) or a group of countries (continents; the EU, the EU and
the United States, NATO, G7, Five Eyes, the Commonwealth, the Visegrád Group,
Nordic, Baltic and Benelux countries, the former Soviet Union, Mercosur, the
Arab League, ASEAN; see [`viewer/groups.py`](viewer/groups.py)), by text (English or local name, national code, folder
name), or show only signs that 2+ countries have. Within each type, signs can
be sorted by how many of the chosen countries have them (most or fewest
first) or by name. Click a sign to see each
country's image large, with all its names, the national code, author, licence
and earlier (archived) images. Every sign has its own link, e.g.
`#warning/bend-left`, and the filters are kept in the URL
(`?type=warning&q=bend&countries=sk,cz&sort=countries-desc`), so a filtered list can be bookmarked. While
any filter differs from a first visit, **Reset filters** (next to the
filters, and under "No signs match") brings back every type and country.
Sign images stand on one line at their bottom edge, in the list and in a
sign's detail, so their shapes and sizes are easy to compare.

**Share** (in the header, next to each category and in a sign's detail)
opens the phone's share sheet, or copies the link on a computer. Links point
at small pages under `share/`, one per sign (`share/warning/bend-left/`) and
per category (`share/warning/`), whose title, description and picture are
what messengers and social networks show as the link preview; they send the
visitor on to the sign or category. The builder writes them with absolute
links for `--site-url` (default `$SITE_URL`, else
`https://skifahrer.github.io/traffic-signs/`).
The page preloads `data.json` from its first line, and while it downloads, a
progress bar shows how much has arrived over placeholder rows shaped like the
list. Each sign image shimmers as a placeholder until it has loaded. The
list then shows the first 100 matching signs and adds the next 100 as you scroll
(or with *Show more*); the header counts how many are shown, e.g.
*200 of 1,314 signs*.
Images stored as TIFF, which browsers do not display, are shown through the
PNG thumbnail that Wikimedia Commons renders for them.

The site is built from `signs/` by `python3 -m viewer` (static page in
[`viewer/static`](viewer/static), data in `data.json`) and published by
[`.github/workflows/pages.yml`](.github/workflows/pages.yml) from master: on
every change to `signs/` or the viewer, after every run of the sync workflow
(which commits its changes to master), and on demand. On phones the filters fold
under *Filters* and each sign is a card: the countries wrap onto as many lines
as needed, so nothing scrolls sideways, and a country without the sign keeps
its place as an empty slot, so each country is in the same spot on every card. One-time setup: *Settings → Pages → Build and
deployment → Source: GitHub Actions*.

To preview it locally:

```sh
python3 -m viewer --serve   # builds _site/ and serves http://localhost:8000
```

## Countries

Regions of a country have ISO 3166-2 codes (`us-ca`) and run together as one
bundle (`python3 -m pipelines us-states`). In the viewer they are not part of
*All countries*: choose *US states* in the Countries menu, or open the
*US states* chip to tick some of them, or *Select all US states*, next to the
countries.

| Country | Signs | Source | Pipeline |
| --- | --- | --- | --- |
| Australia (`au`) | 285 | [Road signs in Australia](https://en.wikipedia.org/wiki/Road_signs_in_Australia) (English Wikipedia, national AS 1742 signs only) | [`pipelines/countries/au`](pipelines/countries/au) |
| Austria (`at`) | 201 | [Bildtafel der Verkehrszeichen in Österreich](https://de.wikipedia.org/wiki/Bildtafel_der_Verkehrszeichen_in_%C3%96sterreich) (German Wikipedia, StVO §§ 50–54) | [`pipelines/countries/at`](pipelines/countries/at) |
| Belgium (`be`) | 280 | [Verkeersborden in België - Serie A: Gevaarsborden](https://nl.wikipedia.org/wiki/Verkeersborden_in_Belgi%C3%AB_-_Serie_A:_Gevaarsborden) and the pages for the series B–F (Dutch Wikipedia, Wegcode), with [Road signs in Belgium](https://en.wikipedia.org/wiki/Road_signs_in_Belgium) for the signs those lack | [`pipelines/countries/be`](pipelines/countries/be) |
| Canada (`ca`) | 65 | [Road signs in Canada](https://en.wikipedia.org/wiki/Road_signs_in_Canada) (English Wikipedia, national MUTCDC examples only) | [`pipelines/countries/ca`](pipelines/countries/ca) |
| Czechia (`cz`) | 368 | [Seznam dopravních značek v Česku](https://cs.wikipedia.org/wiki/Seznam_dopravn%C3%ADch_zna%C4%8Dek_v_%C4%8Cesku) (Czech Wikipedia, vyhláška 294/2015 Sb.) | [`pipelines/countries/cz`](pipelines/countries/cz) |
| Denmark (`dk`) | 135 | [Vejtavler i Danmark](https://da.wikipedia.org/wiki/Vejtavler_i_Danmark) (Danish Wikipedia, main signs A–E) | [`pipelines/countries/dk`](pipelines/countries/dk) |
| Estonia (`ee`) | 536 | [Eesti liiklusmärgid](https://et.wikipedia.org/wiki/Eesti_liiklusm%C3%A4rgid) (Estonian Wikipedia, codes from the image names) | [`pipelines/countries/ee`](pipelines/countries/ee) |
| Finland (`fi`) | 327 | [Luettelo Suomen liikenteen varoitusmerkeistä](https://fi.wikipedia.org/wiki/Luettelo_Suomen_liikenteen_varoitusmerkeist%C3%A4) and the seven other lists of current signs (Finnish Wikipedia, tieliikennelaki 2020) | [`pipelines/countries/fi`](pipelines/countries/fi) |
| France (`fr`) | 252 | [Panneau de signalisation routière de danger en France](https://fr.wikipedia.org/wiki/Panneau_de_signalisation_routi%C3%A8re_de_danger_en_France) and the other family articles and lists (French Wikipedia) | [`pipelines/countries/fr`](pipelines/countries/fr) |
| Germany (`de`) | 969 | [Bildtafel der Verkehrszeichen in der Bundesrepublik Deutschland seit 2017](https://de.wikipedia.org/wiki/Bildtafel_der_Verkehrszeichen_in_der_Bundesrepublik_Deutschland_seit_2017) (German Wikipedia, VwV-StVO) | [`pipelines/countries/de`](pipelines/countries/de) |
| Great Britain (`gb`) | 280 | [Road signs in the United Kingdom](https://en.wikipedia.org/wiki/Road_signs_in_the_United_Kingdom) (English Wikipedia, TSRGD diagram numbers) | [`pipelines/countries/gb`](pipelines/countries/gb) |
| Greece (`gr`) | 302 | [Πινακίδες οδοσήμανσης στην Ελλάδα](https://el.wikipedia.org/wiki/%CE%A0%CE%B9%CE%BD%CE%B1%CE%BA%CE%AF%CE%B4%CE%B5%CF%82_%CE%BF%CE%B4%CE%BF%CF%83%CE%AE%CE%BC%CE%B1%CE%BD%CF%83%CE%B7%CF%82_%CF%83%CF%84%CE%B7%CE%BD_%CE%95%CE%BB%CE%BB%CE%AC%CE%B4%CE%B1) (Greek Wikipedia, ΚΟΚ) | [`pipelines/countries/gr`](pipelines/countries/gr) |
| Hungary (`hu`) | 379 | [Útjelző táblák Magyarországon](https://hu.wikipedia.org/wiki/%C3%9Atjelz%C5%91_t%C3%A1bl%C3%A1k_Magyarorsz%C3%A1gon) (Hungarian Wikipedia, KRESZ) | [`pipelines/countries/hu`](pipelines/countries/hu) |
| Ireland (`ie`) | 437 | [Road signs in Ireland](https://en.wikipedia.org/wiki/Road_signs_in_Ireland) (English Wikipedia, Traffic Signs Manual codes) | [`pipelines/countries/ie`](pipelines/countries/ie) |
| Netherlands (`nl`) | 200 | [Verkeersborden in Nederland](https://nl.wikipedia.org/wiki/Verkeersborden_in_Nederland) (Dutch Wikipedia, RVV 1990 series A–L) and [Road signs in the Netherlands](https://en.wikipedia.org/wiki/Road_signs_in_the_Netherlands) (English Wikipedia, for the signs only it shows; Dutch names from `translations.csv`) | [`pipelines/countries/nl`](pipelines/countries/nl) |
| Poland (`pl`) | 404 | [Wzory znaków i sygnałów drogowych w Polsce](https://pl.wikipedia.org/wiki/Wzory_znak%C3%B3w_i_sygna%C5%82%C3%B3w_drogowych_w_Polsce) (Polish Wikipedia) | [`pipelines/countries/pl`](pipelines/countries/pl) |
| Portugal (`pt`) | 279 | [Sinalização de trânsito em Portugal](https://pt.wikipedia.org/wiki/Sinaliza%C3%A7%C3%A3o_de_tr%C3%A2nsito_em_Portugal) (Portuguese Wikipedia, Regulamento de Sinalização do Trânsito) | [`pipelines/countries/pt`](pipelines/countries/pt) |
| Romania (`ro`) | 278 | [Indicatoarele rutiere din România](https://ro.wikipedia.org/wiki/Indicatoarele_rutiere_din_Rom%C3%A2nia) (Romanian Wikipedia, codes from the image names) | [`pipelines/countries/ro`](pipelines/countries/ro) |
| Slovakia (`sk`) | 837 | [Zoznam dopravných značiek na Slovensku](https://sk.wikipedia.org/wiki/Zoznam_dopravn%C3%BDch_zna%C4%8Diek_na_Slovensku) (Slovak Wikipedia, VL 6.1 / 6.3 / 6.4) | [`pipelines/countries/sk`](pipelines/countries/sk) |
| US states (`us-states`: `us-al` … `us-wy`, DC, Puerto Rico) | 52 | Each state's route shield, from Wikipedia's road data modules ([`Module:Road data/strings/USA/CA`](https://en.wikipedia.org/wiki/Module:Road_data/strings/USA/CA), …) | [`pipelines/countries/us_states`](pipelines/countries/us_states) |
| Ukraine (`ua`) | 363 | [Дорожні знаки України](https://uk.wikipedia.org/wiki/%D0%94%D0%BE%D1%80%D0%BE%D0%B6%D0%BD%D1%96_%D0%B7%D0%BD%D0%B0%D0%BA%D0%B8_%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D0%B8) (Ukrainian Wikipedia, ДСТУ 4100) | [`pipelines/countries/ua`](pipelines/countries/ua) |
| United States (`us`) | 1,132 | [Road signs in the United States](https://en.wikipedia.org/wiki/Road_signs_in_the_United_States) (English Wikipedia, MUTCD) | [`pipelines/countries/us`](pipelines/countries/us) |

Countries still to add, and in which order, are listed in [COUNTRIES.md](COUNTRIES.md).

## Pipelines

Each country's signs come from a list on Wikipedia. One command syncs every
country, or the ones you name:

```sh
python3 -m pipelines                  # every country
python3 -m pipelines sk               # only Slovakia (several: sk cz de)
python3 -m pipelines --list           # available countries
python3 -m pipelines sk --no-images   # names and metadata only
python3 -m pipelines sk --check       # report what would change, write nothing
python3 -m pipelines sk --prune       # delete signs removed from the page instead of archiving them
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

### Images and the archive

Each run compares the image on disk with Commons by SHA-1. The SHA-1 comes
from the Commons API together with the licence and author (50 files per
request), so images are never downloaded just to compare them; only the local
copy is hashed:

| Situation | What the sync does |
| --- | --- |
| Image not on disk yet | downloads it |
| Commons has a new version (SHA-1 differs) | downloads it over the old one |
| Page shows a `.png`/`.jpg`/`.tif`, Commons has an `.svg` of the same name | downloads the SVG and removes the old file |
| Image deleted from Commons, sign still on the page | renames it to `<sign>-<country>-archived-<year>.<ext>` and moves its metadata to `archived` with `valid_until` |
| Sign removed from the page | archives its image the same way and marks the sign `"valid_until": <year>`; its folder and names stay |
| Sign comes back to the page | downloads the current image and drops the sign's `valid_until`; the archive is kept |
| `translations.csv` gives a code another category or slug | moves the country's folder there (images, archive and name, files renamed); the old sign goes when no country is left in it |

Moving is how two countries' versions of one sign are merged: point the
code at the slug the other countries use and run the sync.

`<year>` is the year the sync noticed the change, so it is the last year the
image was known to be valid. With `--prune`, signs that left the page are
deleted instead of archived.

```json
{
  "sign": "danger",
  "category": "warning",
  "country": "sk",
  "code": "101",
  "valid_until": 2026,
  "archived": [
    {"file": "danger-sk-archived-2026.svg", "sha1": "f3c1…", "source": "https://commons.wikimedia.org/wiki/File:…",
     "author": "…", "license": "Public domain", "license_url": null, "valid_until": 2026}
  ],
  "source": {"pipeline": "sk-wikipedia", "page": "…", "file": "101 Nebezpečenstvo.svg"}
}
```

### Code layout

```
pipelines/
  __main__.py          command line: picks the countries, runs them, writes the report
  core/                shared by every country
    model.py           Source (a country's settings), Entry, Translation, commons_category()
    parsers.py         reusable page readers: gallery(), wikitable()
    sync.py            the sync engine: page → translations → images → signs/
    images.py          image download, update and archiving
    report.py          Markdown report for the job summary and the commit message
    layout.py          the signs/ folder structure
    wikimedia.py       HTTP client with User-Agent, rate limit and retries; Commons category walk
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

   Other options, for pages that are harder to read:

   | Page | Use |
   | --- | --- |
   | Signs spread over several pages | `page=["Panneau … de danger en France", "Panneau … de prescription en France"]`; every parser reads every page, and a sign listed twice counts once: a code found on an earlier page keeps that page's image, so list the local page first |
   | Signs missing from the local page | `"en:Road signs in France"` reads a page from the English (or any other) Wikipedia |
   | Signs missing from every page, but drawn on Commons | `commons_category("Diagrams of road signs of Denmark", exclude=r"(?i)historic\|obsolete")` reads a Commons category as a page that shows all its files, see below |
   | Every caption starts with a word that is not part of the code | `code_prefix=r"(?:Zusatzzeichen\|Zeichen) "` on `gallery()`/`wikitable()` stores `Zeichen 101` as `101` |
   | Captions with a dot, dash or slash after the code | read as they are: `A1a - Virage à droite`, `B0. Circulation interdite`, `RA-9A/Cross other side` |
   | The page also shows older or regional signs | `parsers.between(parser, start=r"^==\s*Categorisation", end=r"^===\s*Obsolete")` reads only that part of the page |
   | Variants share a code in their captions, files are named after the sign | `parsers.named_files(r"MUTCD (?P<code>.+)\.svg", caption_code=r"[A-Z]+\d\S*\s+")`: the code from the gallery image's name, the name from its caption |
   | Captions without codes, but files named after the sign | `parsers.files(r"UK traffic sign (?P<code>.+)\.svg")` takes the code from every matching image on the page |
   | Captions without (usable) local names | `local_names="translations"`: names come from the `name_<language>` column of `translations.csv` |
   | An English-speaking country | `language="en", names_key="en-GB"`: `translations.csv` has `name_en`, the English name every country with the sign shares, and `name_en-GB`, the country's own wording |

   A Commons category (`from ...core.model import commons_category`) is
   read with its subcategories, `depth` levels down (3 by default), each
   file once. `exclude` is a regular expression for subcategory names not to
   enter: historic and obsolete sets, photos, other countries or regions.
   Check its subcategories before you write it: Finland's current signs, for
   one, sit in "Diagrams of historic road signs of Finland, 2020 set". The
   files become one gallery without captions, so read them with
   `parsers.files()`, take the names from `translations.csv`
   (`local_names="translations"`), and list the category after the
   Wikipedia pages: a sign on a page keeps the page's image, and a code that
   appears twice within the category is an error to settle with `ignore` or
   corrections.csv.

   Images: when the page uses a `.png`, `.jpg` or `.tif` and Commons has an
   `.svg` of the same name, the SVG is downloaded instead (`prefer_svg=True`,
   the default).
2. Add `translations.csv` with the columns `code,category,slug,name_en,name_<language>`.
   Reuse an existing sign folder (`slug`) when the sign means the same, so the
   countries line up. The names file is shared, so use the English name and
   category that folder already has; `tests/test_countries.py` fails when two
   countries disagree. Run `python3 -m pipelines <code> --check` to see which
   codes on the page still need a row.
3. Optionally add `corrections.csv` (`file,code,name_<language>,note`).

The command line and the sync workflow find the new country automatically.

### Automatic updates

[`.github/workflows/sync.yml`](.github/workflows/sync.yml) runs every Monday
for all countries, or from the Actions tab: *Sync signs from Wikipedia → Run
workflow*, where the **Country** dropdown offers `all` or a single country,
plus the prune and verbose switches.

The run starts with a **Start** job that runs the tests and picks the
countries. Each country is then its own **Sync <country>** job. They run one
after another, and a failing country does not stop the next. Each job commits
its changes straight to the branch the workflow runs on (master for the weekly
run) as `github-actions[bot]`. The commit message has the counts (new, changed,
images downloaded, archived, ...) and a link to the run, and the job summary
has the full report. A job with nothing new makes no commit. Signs written
before an error are committed too, and the job still fails, so check its
summary. Once the run finishes, the viewer is republished.

When you add a country, add it to the dropdown's `options` in `sync.yml` too;
`tests/test_workflow.py` fails until the list matches `pipelines/countries`.
If master is protected by a branch rule, allow GitHub Actions to push to it,
or the job fails with "Could not push".

## Licence

The repository's own content (structure, names, metadata, code) is
[CC0 1.0](LICENSE). Images keep the licence of their source, recorded in each
sign's `.json` under `image.license`. The Slovak sign drawings on Wikimedia
Commons are official works of the Slovak government and in the public domain
(`PD-SlovakGov`).
