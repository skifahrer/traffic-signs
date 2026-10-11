"""Registry of country pipelines.

Each country is a sub-package named after its ISO 3166-1 alpha-2 code
(`sk`, `cz`, `pl`, ...) whose `__init__.py` defines `SOURCE`, plus its
translations.csv and corrections.csv. Adding the package is all it takes for
`python -m pipelines` and the sync workflow to pick it up.

A package can instead define `SOURCES`, one per region of a country, with
ISO 3166-2 codes in lowercase ("us-ca", "us-tx") and a common `bundle` name
("us-states") under which they run together.
"""

from __future__ import annotations

import importlib
import pkgutil

from ..core.model import Source


def _packages() -> list[tuple[str, object]]:
    return [
        (module.name, importlib.import_module(f"{__name__}.{module.name}"))
        for module in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name)
        if module.ispkg
    ]


def all_sources() -> dict[str, Source]:
    """Every source, keyed by its country or region code."""
    sources = {}
    for name, package in _packages():
        for source in getattr(package, "SOURCES", None) or [package.SOURCE]:
            expected = source.country.startswith(f"{source.bundle.split('-')[0]}-") if source.bundle else source.country == name
            if not expected:
                raise ValueError(f"countries/{name} declares country {source.country!r}")
            sources[source.country] = source
    return sources


def bundles(sources: dict[str, Source]) -> dict[str, list[str]]:
    """Regions run together, by bundle name: {"us-states": ["us-al", ...]}."""
    found: dict[str, list[str]] = {}
    for code, source in sources.items():
        if source.bundle:
            found.setdefault(source.bundle, []).append(code)
    return found


def choices(sources: dict[str, Source]) -> list[str]:
    """What can be run on its own: each country, and each bundle as a whole."""
    return sorted([code for code, source in sources.items() if not source.bundle] + list(bundles(sources)))
