"""
Guards against shipping an app whose front-end files are missing.

A `build/` rule in .gitignore once silently kept Three.js's own build/
folder out of git: everything worked on the author's disk, CI stayed
green, and the released app's page failed to load. These tests check what
GIT actually has, not just what is on disk.

Run with:  uv run pytest
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "frontend"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return set(out.split("\n")) - {""}


def referenced_vendor_paths():
    """Every /static/vendor/... file index.html loads, plus the imports
    inside the vendored Three.js modules."""
    html = (FRONTEND / "index.html").read_text()
    # (import-map prefixes ending in '/' are directories, not files)
    paths = {
        p for p in re.findall(r'/static/(vendor/[^"\')\s]+)', html) if not p.endswith("/")
    }

    # ES-module imports in Three's vendored files (relative './x.js').
    for rel in list(paths):
        f = FRONTEND / rel
        if f.suffix == ".js" and "three" in f.parts:
            for imp in re.findall(r'from\s*["\'](\./[^"\']+)["\']', f.read_text()):
                paths.add(str((f.parent / imp).resolve().relative_to(FRONTEND)))
    return paths


def test_every_vendor_file_the_page_needs_is_committed():
    tracked = tracked_files()
    missing = [
        p for p in sorted(referenced_vendor_paths()) if f"frontend/{p}" not in tracked
    ]
    assert not missing, f"referenced by the page but not in git: {missing}"


def test_app_js_imports_resolve_to_committed_files():
    tracked = tracked_files()
    html = (FRONTEND / "index.html").read_text()
    mapping = dict(re.findall(r'"(three(?:/addons/)?)":\s*"/static/([^"]+)"', html))
    js = (FRONTEND / "app.js").read_text()

    for spec in re.findall(r"from\s+'(three[^']*)'", js):
        if spec == "three":
            target = mapping["three"]
        else:
            target = mapping["three/addons/"] + spec[len("three/addons/"):]
        assert f"frontend/{target}" in tracked, f"{spec} -> {target} is not in git"
