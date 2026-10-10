"""Progress logging for the pipelines.

Everything goes to stderr with the time since start, so the Markdown report on
stdout stays clean. On GitHub Actions, phases become collapsible log groups and
warnings/errors become annotations on the run.
"""

from __future__ import annotations

import contextlib
import os
import sys
import time

_START = time.monotonic()
_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"
verbose = False


def elapsed() -> float:
    return time.monotonic() - _START


def duration(seconds: float) -> str:
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def info(message: str) -> None:
    print(f"[{duration(elapsed()):>7}] {message}", file=sys.stderr, flush=True)


def detail(message: str) -> None:
    """Only shown with --verbose."""
    if verbose:
        info(message)


def warning(message: str) -> None:
    info(f"WARNING: {message}")
    if _ACTIONS:
        print(f"::warning::{_escape(message)}", file=sys.stderr, flush=True)


def error(message: str) -> None:
    info(f"ERROR: {message}")
    if _ACTIONS:
        print(f"::error::{_escape(message)}", file=sys.stderr, flush=True)


@contextlib.contextmanager
def phase(title: str):
    """A named step; logs how long it took."""
    if _ACTIONS:
        print(f"::group::{title}", file=sys.stderr, flush=True)
    info(f"== {title}")
    started = time.monotonic()
    try:
        yield
    finally:
        info(f"== {title}: done in {duration(time.monotonic() - started)}")
        if _ACTIONS:
            print("::endgroup::", file=sys.stderr, flush=True)


class Progress:
    """`[12/837]` counters with an ETA based on the items processed so far."""

    def __init__(self, total: int):
        self.total = total
        self.done = 0
        self.started = time.monotonic()

    def step(self) -> str:
        self.done += 1
        return f"[{self.done:>{len(str(self.total))}}/{self.total}]"

    def eta(self) -> str:
        if not self.done:
            return "?"
        rate = (time.monotonic() - self.started) / self.done
        return duration(rate * (self.total - self.done))


def _escape(message: str) -> str:
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
