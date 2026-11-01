"""Tests for the update check (app/updates.py) and its two endpoints."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import main, updates  # noqa: E402

GOOD_URL = "https://github.com/whatder1/EZPy2STL/releases/tag/v0.8.0"


def release(tag="v0.8.0", url=GOOD_URL, **extra):
    return {"tag_name": tag, "html_url": url, "draft": False, "prerelease": False, **extra}


@pytest.fixture()
def enabled(monkeypatch):
    monkeypatch.delenv("EZPY2STL_NO_UPDATE_CHECK")


@pytest.mark.parametrize("text,expected", [
    ("v0.7.2", (0, 7, 2)), ("0.7.2", (0, 7, 2)), ("1.0", (1, 0)),
    ("0.8.0-rc1", None), ("", None), (None, None), ("latest", None),
])
def test_parse_version(text, expected):
    assert updates.parse_version(text) == expected


def test_numeric_not_string_comparison():
    assert updates.parse_version("0.10.0") > updates.parse_version("0.9.9")


def test_newer_release_is_offered(enabled):
    info = updates.check_for_update(fetch=lambda: release(), current="0.7.2")
    assert info == {"update_available": True, "current": "0.7.2", "latest": "0.8.0", "url": GOOD_URL}


@pytest.mark.parametrize("tag", ["v0.7.2", "v0.7.1", "v0.7.2-rc1"])
def test_same_older_or_odd_release_is_ignored(enabled, tag):
    assert not updates.check_for_update(fetch=lambda: release(tag), current="0.7.2")["update_available"]


@pytest.mark.parametrize("extra", [{"prerelease": True}, {"draft": True}])
def test_prereleases_and_drafts_are_ignored(enabled, extra):
    assert not updates.check_for_update(fetch=lambda: release(**extra), current="0.7.2")["update_available"]


def test_foreign_url_is_ignored(enabled):
    bad = release(url="https://evil.example.com/releases/tag/v0.8.0")
    assert not updates.check_for_update(fetch=lambda: bad, current="0.7.2")["update_available"]


def test_network_failure_is_silent(enabled):
    def boom():
        raise OSError("offline")
    assert updates.check_for_update(fetch=boom, current="0.7.2") == {"update_available": False}


def test_unknown_current_version_is_silent(enabled):
    assert not updates.check_for_update(fetch=lambda: release(), current="not-a-version")["update_available"]


def test_opt_out_env_var_never_fetches(monkeypatch):
    monkeypatch.setenv("EZPY2STL_NO_UPDATE_CHECK", "1")

    def must_not_run():
        raise AssertionError("fetched despite opt-out")
    assert not updates.check_for_update(fetch=must_not_run, current="0.7.2")["update_available"]


def test_dev_version_is_read_from_pyproject():
    assert updates.parse_version(updates.current_version()) is not None


# ---- endpoints ----

@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(main, "_update_info", None)
    return TestClient(main.app)


def test_endpoint_reports_and_caches(client, monkeypatch):
    calls = []
    monkeypatch.setattr(main.updates, "check_for_update",
                        lambda: calls.append(1) or {"update_available": True, "url": GOOD_URL,
                                                    "current": "0.7.2", "latest": "0.8.0"})
    assert client.get("/update-check").json()["latest"] == "0.8.0"
    client.get("/update-check")
    assert len(calls) == 1


def test_open_page_refuses_without_an_update(client):
    assert client.post("/open-update-page").status_code == 404


def test_open_page_only_opens_the_validated_url(client, monkeypatch):
    opened = []
    monkeypatch.setattr(main.subprocess, "run", lambda cmd, **kw: opened.append(cmd))
    monkeypatch.setattr(main, "_update_info", {"update_available": True, "url": GOOD_URL})
    # a body or query pretending to supply a different URL is ignored
    assert client.post("/open-update-page?url=https://evil.example.com").status_code == 200
    assert opened == [["open", GOOD_URL]]
    monkeypatch.setattr(main, "_update_info",
                        {"update_available": True, "url": "https://evil.example.com/x"})
    assert client.post("/open-update-page").status_code == 404
