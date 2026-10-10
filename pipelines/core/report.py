"""The Markdown report of a sync run (job summary and pull request body)."""

from __future__ import annotations

import os

from . import layout
from .sync import Result

SECTION_LIMIT = 100  # keeps the PR body under GitHub's size limit


def render(results: list[Result]) -> str:
    return "\n".join(_render_one(result) for result in results)


def _render_one(r: Result) -> str:
    source = r.source
    translations = os.path.relpath(source.translations_file, layout.REPO_ROOT)
    lines = [
        f"## {source.country_name} ({source.country}) from [Wikipedia]({source.page_url})",
        "",
        f"- Signs on the page: {r.entries}",
        f"- Synced (have a translation): {r.synced}",
        f"- New: {len(r.added)}, metadata changed: {len(r.changed)}, images downloaded: {len(r.images)}",
        f"- No longer on the page: {len(r.removed)}" + (" (deleted)" if r.options.prune and r.removed else ""),
        f"- Waiting for a translation: {len(r.untranslated)}",
        "",
    ]

    def section(title: str, items: list[str]) -> None:
        if items:
            shown = [f"- {item}" for item in items[:SECTION_LIMIT]]
            if len(items) > SECTION_LIMIT:
                shown.append(f"- … and {len(items) - SECTION_LIMIT} more")
            lines.extend([f"### {title}", "", *shown, ""])

    section("Errors", r.errors)
    section(
        f"Missing translations (add them to {translations})",
        [f"`{e.code}` {e.name} (`{e.file}`)" for e in r.untranslated],
    )
    section(f"{source.language_name} name changed, check the English translation", r.renamed)
    section("New signs", r.added)
    section("Changed metadata", r.changed)
    section(
        "Removed from the page" + ("" if r.options.prune else " (run with --prune to delete)"),
        [f"`{key}`" for key in r.removed],
    )
    section("Translations whose code is no longer on the page", [f"`{code}`" for code in r.unused])
    return "\n".join(lines)
