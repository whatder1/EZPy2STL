"""
Update check: asks GitHub whether a newer release exists.

This only NOTIFIES. The app is not code-signed or notarized, so it can't
safely replace itself; instead the banner opens the release page and the
user installs the new DMG as usual.

Privacy: one HTTPS request to api.github.com per launch, no identifiers
sent. Set EZPY2STL_NO_UPDATE_CHECK=1 to turn it off.
"""

import json
import os
import plistlib
import re
import sys
import urllib.request
from pathlib import Path

REPO = "whatder1/EZPy2STL"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PREFIX = f"https://github.com/{REPO}/releases/"


def current_version() -> str | None:
    """Packaged app: the bundle's Info.plist (the release workflow already
    checks it against the tag). Dev checkout: pyproject.toml."""
    if getattr(sys, "frozen", False):
        plist = Path(sys.executable).resolve().parents[1] / "Info.plist"
        try:
            with open(plist, "rb") as fh:
                return plistlib.load(fh).get("CFBundleShortVersionString")
        except (OSError, ValueError):
            return None
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(), re.M)
    except OSError:
        return None
    return match.group(1) if match else None


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """'v0.7.2' / '0.7.2' -> (0, 7, 2). Anything odd (e.g. '0.8.0-rc1') -> None,
    so a pre-release string is never offered as an update."""
    if not text:
        return None
    match = re.fullmatch(r"v?(\d+(?:\.\d+){1,3})", text.strip())
    return tuple(int(p) for p in match.group(1).split(".")) if match else None


def fetch_latest_release() -> dict | None:
    request = urllib.request.Request(
        LATEST_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "EZPy2STL-update-check"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def check_for_update(fetch=fetch_latest_release, current=None) -> dict:
    """Never raises: any failure just means 'no update to show'."""
    none = {"update_available": False}
    if os.environ.get("EZPY2STL_NO_UPDATE_CHECK"):
        return none
    current = current if current is not None else current_version()
    have = parse_version(current)
    if have is None:
        return none
    try:
        release = fetch()
    except Exception:
        return none
    if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
        return none
    latest = release.get("tag_name")
    want = parse_version(latest)
    url = release.get("html_url", "")
    if want is None or want <= have or not url.startswith(RELEASES_PREFIX):
        return none
    return {
        "update_available": True,
        "current": current,
        "latest": latest.lstrip("v"),
        "url": url,
    }
