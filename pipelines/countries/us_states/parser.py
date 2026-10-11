"""Reads a US state's route shield from its Wikipedia road data module.

Wikipedia draws route shields ({{jct}}, infoboxes) from one Lua data module
per state, "Module:Road data/strings/USA/CA", where the state's own route
type names its shield file with the route number left out:

    CA.SR = {
        shield = "California %route%.svg",
        name = "State Route %route%",
        ...
    }
    CA.CA = CA.SR

The type named after the state (CA.CA) is its state routes; following it to
CA.SR gives the shield. Shields can also be `{default = "…", ["162"] = …}`
for routes drawn differently, `{below = "…", above = "… wide.svg"}` for
shields that widen for longer numbers, a `local` holding the file name, or
point at another type (`MI.M.shield`).
The sign's code is the route type ("SR", "SH", "M"), and the image is the
shield of one route, whose number the state's Source gives.
"""

from __future__ import annotations

import re

from ...core.model import Entry, Parser, Problem


def shield_parser(state: str, route: str) -> Parser:
    """A parser for the module of `state` ("CA"), giving the shield of route `route`."""

    def parse(wikitext: str) -> tuple[list[Entry], list[Problem]]:
        kind = _main_type(wikitext, state)
        body = _table(wikitext, state, kind) if kind else None
        shield = _value(wikitext, state, body, "shield", route) if body else None
        if not shield or "%route%" not in shield:
            return [], [Problem(file="", message=f"no state route shield found in the module for {state}")]
        name = _value(wikitext, state, body, "name", route) or f"{kind} %route%"
        return [Entry(file=shield.replace("%route%", route), code=kind, name=name.replace("%route%", route))], []

    parse.__name__ = f"shield_parser({state!r})"
    return parse


def _main_type(text: str, state: str) -> str | None:
    """The type the state's own name points at: "SR" for `CA.CA = CA.SR`."""
    s = re.escape(state)
    alias = re.search(rf"^{s}\.{s}\s*=\s*{s}\.(\w+)\s*$", text, re.MULTILINE) or re.search(
        rf'^{s}\.{s}\s*=\s*{s}\["([^"]+)"\]\s*$', text, re.MULTILINE
    )
    if alias:
        return alias.group(1)
    if re.search(rf"^{s}\.{s}\s*=\s*\{{", text, re.MULTILINE):
        return state
    for kind in ("SR", "SH", "Route"):
        if re.search(rf"^{s}\.{kind}\s*=\s*\{{", text, re.MULTILINE):
            return kind
    return None


def _table(text: str, state: str, kind: str) -> str | None:
    """The `{…}` of `CA.SR = {…}`, matching braces."""
    s = re.escape(state)
    start = re.search(rf'^{s}(?:\.{re.escape(kind)}|\["{re.escape(kind)}"\])\s*=\s*\{{', text, re.MULTILINE)
    if not start:
        return None
    return _braces(text, start.end() - 1)


def _braces(text: str, i: int) -> str | None:
    """What is inside the `{` at `i` and its matching `}`."""
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1 : j]
    return None


def _value(text: str, state: str, body: str, key: str, route: str) -> str | None:
    """A field of a type's table: a string, a table's choice for `route`, a local or another type's field."""
    s = re.escape(state)
    found = re.search(rf"^\s*{key}\s*=\s*(.+?),?\s*$", body, re.MULTILINE)
    if not found:
        return None
    value = found.group(1).strip(", ")
    if value.startswith('"'):
        return value.strip('"')
    if value.startswith("{"):
        return _choice(text, _braces(body, body.index("{", found.start())) or "", route)
    other = re.fullmatch(rf"{s}\.(\w+)\.{key}", value)
    if other:
        table = _table(text, state, other.group(1))
        return _value(text, state, table, key, route) if table else None
    return _local(text, value)


def _choice(text: str, table: str, route: str) -> str | None:
    """The shield a table picks for `route`.

    {default = …}; {hook = "splitlen", below = …, above = …} for shields that
    widen for longer numbers; {hook = "between", lower = 20, upper = 100,
    yes = …, no = …} for a range of numbers drawn differently.
    """
    field = lambda name: re.search(rf'^\s*{name}\s*=\s*("[^"]+"|\w+)', table, re.MULTILINE)  # noqa: E731
    between = re.search(r'hook\s*=\s*"between"', table)
    if between:
        lower, upper = (int(field(n).group(1)) for n in ("lower", "upper"))
        names = ("yes",) if lower <= int(route) < upper else ("no",)
    else:
        names = ("default", "below")
    for name in names:
        found = field(name)
        if found:
            value = found.group(1)
            return value.strip('"') if value.startswith('"') else _local(text, value)
    return None


def _local(text: str, name: str) -> str | None:
    """The string a `local name = "…"` holds."""
    found = re.search(rf'^local\s+{re.escape(name)}\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return found.group(1) if found else None
