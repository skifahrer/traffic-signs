"""Traffic signs' checks for `tools/ready.py`: ruff, then the unit tests."""

from ready import Check

RUFF = "ruff==0.16.10"

CHECKS = [
    Check("ready's tests", ["python3", "tools/test-ready.py"], covers=("tools/*ready*",)),
    Check("ruff", ["ruff", "check", "."], covers=("*.py", "ruff.toml"), tool=RUFF),
    Check("format", ["ruff", "format", "--check"], covers=("*.py",), tool=RUFF, on_paths=True),
    Check(
        "unit tests",
        ["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        covers=("*.py", "signs/*", "names/*", "regulations/*", "pipelines/*", "viewer/*"),
        waits=True,
    ),
]
