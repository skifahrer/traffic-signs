"""Registry of country pipelines.

Each country is a sub-package named after its ISO 3166-1 alpha-2 code
(`sk`, `cz`, `pl`, ...) whose `__init__.py` defines `SOURCE`, plus its
translations.csv and corrections.csv. Adding the package is all it takes for
`python -m pipelines` and the sync workflow to pick it up.
"""

from __future__ import annotations

import importlib
import pkgutil

from ..core.model import Source


def all_sources() -> dict[str, Source]:
    sources = {}
    for module in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if module.ispkg:
            source = importlib.import_module(f"{__name__}.{module.name}").SOURCE
            if source.country != module.name:
                raise ValueError(f"countries/{module.name} declares country {source.country!r}")
            sources[module.name] = source
    return sources
