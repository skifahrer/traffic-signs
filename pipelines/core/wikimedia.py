"""Small, dependency-free client for the Wikimedia endpoints the pipelines use.

Wikimedia asks automated clients to send a descriptive User-Agent, to keep
requests serial and to back off on 429/5xx responses
(https://meta.wikimedia.org/wiki/User-Agent_policy,
https://www.mediawiki.org/wiki/API:Etiquette). Everything here goes through
`Client.get`, which does exactly that.
"""

from __future__ import annotations

import email.utils
import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import log

DEFAULT_USER_AGENT = (
    "traffic-signs-sync/1.0 (https://github.com/skifahrer/traffic-signs) python-urllib"
)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


class Client:
    def __init__(self, user_agent: str | None = None, delay: float = 1.0, retries: int = 6):
        self.user_agent = user_agent or os.environ.get("WIKIMEDIA_USER_AGENT") or DEFAULT_USER_AGENT
        self.delay = delay
        self.retries = retries
        self._last = 0.0

    def get(self, url: str, params: dict | None = None, post: dict | None = None) -> bytes:
        """GET `url` with query `params`, or POST `post` as a form when given."""
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        body = urllib.parse.urlencode(post).encode() if post is not None else None
        for attempt in range(self.retries + 1):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            request = urllib.request.Request(url, data=body, headers={"User-Agent": self.user_agent})
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return response.read()
            except urllib.error.HTTPError as err:
                if err.code not in (429, 500, 502, 503, 504) or attempt == self.retries:
                    raise
                backoff = _retry_after(err) or min(2 ** (attempt + 2), 120)
                reason = f"HTTP {err.code}"
            except (urllib.error.URLError, TimeoutError) as err:
                if attempt == self.retries:
                    raise
                backoff = min(2 ** (attempt + 2), 120)
                reason = str(getattr(err, "reason", err))
            log.info(
                f"    {reason}, retry {attempt + 1}/{self.retries} in {backoff:.0f}s: {url.split('?')[0]}"
            )
            time.sleep(backoff)
        raise AssertionError("unreachable")

    def get_json(self, url: str, params: dict) -> dict:
        # POST, because 50 long file titles do not fit in a GET URL (HTTP 414).
        return json.loads(self.get(url, post={**params, "format": "json", "formatversion": "2"}))

    def page_wikitext(self, wiki: str, title: str) -> str:
        """Raw wikitext of the current revision of `title` on e.g. sk.wikipedia.org."""
        return self.get(f"https://{wiki}/w/index.php", {"title": title, "action": "raw"}).decode("utf-8")

    def image_info(self, api: str, titles: list[str]) -> dict[str, dict]:
        """imageinfo (url, sha1, licence, author) keyed by the title as given.

        Titles that do not exist on that wiki are left out of the result.
        """
        result: dict[str, dict] = {}
        batches = (len(titles) + 49) // 50
        for number, start in enumerate(range(0, len(titles), 50), 1):
            batch = titles[start : start + 50]
            log.info(f"  {urllib.parse.urlparse(api).netloc}: batch {number}/{batches} ({len(batch)} files)")
            data = self.get_json(
                api,
                {
                    "action": "query",
                    "titles": "|".join(batch),
                    "prop": "imageinfo",
                    "iiprop": "url|sha1|mime|extmetadata",
                    "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit",
                    "redirects": "1",
                },
            )
            query = data.get("query", {})
            # Map every requested title through normalisation and redirects.
            alias = {t: t for t in batch}
            for step in ("normalized", "redirects"):
                for item in query.get(step, []):
                    for original, current in list(alias.items()):
                        if current == item["from"]:
                            alias[original] = item["to"]
            pages = {p["title"]: p for p in query.get("pages", [])}
            for original, current in alias.items():
                page = pages.get(current)
                if not page or page.get("missing") or not page.get("imageinfo"):
                    continue
                info = page["imageinfo"][0]
                meta = info.get("extmetadata", {})
                result[original] = {
                    "title": current,
                    "url": info["url"],
                    "description_url": info["descriptionurl"],
                    "sha1": info["sha1"],
                    "mime": info.get("mime"),
                    "license": _meta(meta, "LicenseShortName"),
                    "license_url": _meta(meta, "LicenseUrl"),
                    "author": _meta(meta, "Artist"),
                }
        return result


def sha1_of(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    digest = hashlib.sha1()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_markup(text: str) -> str:
    """Plain text from a short piece of wikitext or HTML (captions, licence fields)."""
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)  # footnotes
    while re.search(r"\{\{[^{}]*\}\}", text):  # templates such as {{refn|...}}, innermost first
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"<br\s*/?\s*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _meta(meta: dict, key: str) -> str | None:
    value = meta.get(key, {}).get("value")
    return strip_markup(value) if value else None


def _retry_after(err: urllib.error.HTTPError) -> float | None:
    value = err.headers.get("Retry-After") if err.headers else None
    if not value:
        return None
    if value.isdigit():
        return float(value)
    parsed = email.utils.parsedate_to_datetime(value)
    return max(parsed.timestamp() - time.time(), 1.0) if parsed else None
