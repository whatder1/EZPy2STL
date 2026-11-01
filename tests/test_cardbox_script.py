"""
Smoke test for the card-box build123d script (tests/fixtures/cardbox.py).

Purpose: catch a build123d upgrade that breaks real-world scripts. The script
is run for real in a scratch folder, with DeprecationWarnings raised by the
script itself turned into errors -- so a call build123d has deprecated (like
`add()` -> `insert()`) fails here long before a later release removes it.

Each variant takes several seconds; they run in parallel-free sequence.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

SCRIPT = Path(__file__).resolve().parent / "fixtures" / "cardbox.py"


def run_script(tmp_path, overrides):
    text = SCRIPT.read_text()
    for name, value in overrides.items():
        text, n = re.subn(
            rf"^{name}(\s*)=\s*[^#\n]*?(\s*#.*)?$",
            lambda m: f"{name}{m.group(1)}= {value}{m.group(2) or ''}",
            text, count=1, flags=re.M)
        assert n == 1, f"setting {name} not found in the fixture"
    script = tmp_path / "model.py"
    script.write_text(text)
    return subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning:__main__", str(script)],
        cwd=tmp_path, capture_output=True, text=True, timeout=600)


@pytest.fixture()
def logo(tmp_path):
    img = Image.new("RGB", (240, 120), "white")
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 110, 110), fill="black")
    d.rectangle((130, 30, 230, 90), fill="black")
    path = tmp_path / "logo.png"
    img.save(path)
    return path


def check(tmp_path, overrides, lid_file):
    result = run_script(tmp_path, overrides)
    assert result.returncode == 0, result.stderr[-1500:]
    assert (tmp_path / "CardboxUSPoker_flat.stl").stat().st_size > 10_000
    assert (tmp_path / lid_file).stat().st_size > 1_000


def test_default_settings(tmp_path):
    check(tmp_path, {}, "CardboxLid_named.stl")


def test_blank_lid(tmp_path):
    check(tmp_path, {"LID_ART": '"blank"'}, "CardboxLid_blank.stl")


def test_two_decks_honeycomb_solid_art(tmp_path):
    check(tmp_path, {"HEX_PATTERN": "True", "NUM_DECKS": "2"}, "CardboxLid_named.stl")


def test_honeycomb_engraved_hugging_plate(tmp_path):
    check(tmp_path, {"HEX_PATTERN": "True", "LID_ART_STYLE": '"engraved_plate"',
                     "PLATE_SHAPE": '"hug"'}, "CardboxLid_named.stl")


def test_image_lid_with_honeycomb(tmp_path, logo):
    check(tmp_path, {"HEX_PATTERN": "True", "LID_ART": '"image"',
                     "LID_IMAGE": f'"{logo}"'}, "CardboxLid_named.stl")
