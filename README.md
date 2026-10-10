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
      <country>/              ISO 3166-1 alpha-2 code, lowercase: sk, cz, us, ...
        <sign>-<country>.svg  the image (svg, png, ...)
        <sign>-<country>.sk   the local name, one file per language (ISO 639-1 code)
        <sign>-<country>.json metadata: national code, names, image source and licence
```

For example:

```
signs/warning/danger/sk/
  danger-sk.svg    the sign
  danger-sk.sk     "Nebezpečenstvo"
  danger-sk.json   {"code": "101", "name": {"en": "Other danger", "sk": "Nebezpečenstvo"}, "image": {...}}
```

The language file holds the sign's official name in that language, nothing
else (UTF-8, one line). Countries with several official languages get one file
per language, e.g. `give-way-ch.de`, `give-way-ch.fr`, `give-way-ch.it`.

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
| Slovakia (`sk`) | 837 | [Zoznam dopravných značiek na Slovensku](https://sk.wikipedia.org/wiki/Zoznam_dopravn%C3%BDch_zna%C4%8Diek_na_Slovensku) (Slovak Wikipedia, VL 6.1 / 6.3 / 6.4) | [`pipelines/sk_wikipedia`](pipelines/sk_wikipedia) |

## Slovak pipeline

`pipelines/sk_wikipedia` reads every gallery entry on the Slovak Wikipedia list
(`Súbor:<file>|<code> <Slovak name>`), and for each one writes the Slovak name,
the metadata and the SVG from Wikimedia Commons into `signs/`.

```sh
python3 -m pipelines.sk_wikipedia               # full sync: names, metadata, images
python3 -m pipelines.sk_wikipedia --no-images   # names and metadata only
python3 -m pipelines.sk_wikipedia --check       # report what would change, write nothing
python3 -m pipelines.sk_wikipedia --prune       # also delete signs removed from the page
```

It needs Python 3.9+ and nothing else. Images are only downloaded when their
SHA-1 on Commons differs from the file on disk, so a re-run is cheap.

The pipeline's data files:

- [`translations.csv`](pipelines/sk_wikipedia/translations.csv): the Slovak sign
  code → category, English folder name and English name. A sign whose code is
  missing here is reported and skipped. Add a row and re-run. The `name_sk`
  column is the Slovak name the translation was made from; when Wikipedia
  renames a sign, the report asks you to check the English name.
- [`corrections.csv`](pipelines/sk_wikipedia/corrections.csv): fixes for
  mistakes on the Wikipedia page (wrong or duplicate codes in captions), keyed
  by image file name.

### Automatic updates

[`.github/workflows/sync-sk-wikipedia.yml`](.github/workflows/sync-sk-wikipedia.yml)
runs the sync every Monday, or on demand from the Actions tab. It opens (or
updates) a pull request on the `sync/sk-wikipedia` branch with the changes and a
report listing new, changed, removed and untranslated signs. For it to open
pull requests, enable *Settings → Actions → General → Allow GitHub Actions to
create and approve pull requests*.

## Licence

The repository's own content (structure, names, metadata, code) is
[CC0 1.0](LICENSE). Images keep the licence of their source, recorded in each
sign's `.json` under `image.license`. The Slovak sign drawings on Wikimedia
Commons are official works of the Slovak government and in the public domain
(`PD-SlovakGov`).
