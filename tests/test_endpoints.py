"""
Tests for the FastAPI layer in app/main.py: the file-serving whitelist
(the thing standing between a request and arbitrary files on disk), the
localhost-only Host check, and the autosave endpoints.

Run with:  uv run pytest
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import executor, main  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Never touch the real workspace or autosave file from a test.
    monkeypatch.setattr(main, "AUTOSAVE_PATH", tmp_path / ".autosave.py")
    monkeypatch.setattr(main, "WORKSPACE", tmp_path)
    monkeypatch.setattr(main, "_last_build_files", {})
    return TestClient(main.app)


# ------------------------------------------------------------
# Health marker + Host check
# ------------------------------------------------------------

def test_healthz_identifies_the_app(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"app": "EZPy2STL"}


@pytest.mark.parametrize("host", ["127.0.0.1:54321", "localhost:8000", "localhost"])
def test_localhost_hosts_are_accepted(client, host):
    assert client.get("/healthz", headers={"host": host}).status_code == 200


@pytest.mark.parametrize(
    "host",
    ["evil.example.com", "evil.example.com:8000", "127.0.0.1.evil.com", "192.168.1.5:8000"],
)
def test_foreign_hosts_are_rejected(client, host):
    """DNS-rebinding defence: a page on another domain that resolves to
    127.0.0.1 still sends its own hostname in the Host header."""
    assert client.get("/healthz", headers={"host": host}).status_code == 400


def test_foreign_host_cannot_run_a_build(client):
    response = client.post(
        "/build",
        json={"script": 'open("x.stl", "w").write("pwned")'},
        headers={"host": "evil.example.com"},
    )
    assert response.status_code == 400


# ------------------------------------------------------------
# File-serving whitelist
# ------------------------------------------------------------

@pytest.mark.parametrize("route", ["/model", "/download"])
def test_unknown_names_are_404(client, route):
    assert client.get(f"{route}/nope.stl").status_code == 404


@pytest.mark.parametrize(
    "name",
    ["..%2F..%2Fetc%2Fpasswd", "%2Fetc%2Fpasswd", "sub%2F..%2F..%2Fsecret.stl"],
)
@pytest.mark.parametrize("route", ["/model", "/download"])
def test_path_escape_attempts_are_404(client, route, name):
    assert client.get(f"{route}/{name}").status_code == 404


def test_only_files_from_the_last_build_are_served(client, tmp_path, monkeypatch):
    built = tmp_path / "box.stl"
    built.write_bytes(b"solid box")
    secret = tmp_path / "secret.txt"
    secret.write_text("do not serve")

    monkeypatch.setattr(main, "_last_build_files", {"box.stl": built})

    assert client.get("/model/box.stl").content == b"solid box"
    assert client.get("/download/box.stl").status_code == 200
    # Exists on disk, but was never produced by a build -> not served.
    assert client.get("/model/secret.txt").status_code == 404
    assert client.get("/download/secret.txt").status_code == 404


def test_listed_but_deleted_file_is_404(client, tmp_path, monkeypatch):
    gone = tmp_path / "gone.stl"
    monkeypatch.setattr(main, "_last_build_files", {"gone.stl": gone})
    assert client.get("/model/gone.stl").status_code == 404


def test_open_in_slicer_rejects_unknown_names(client):
    assert client.post("/open-in-slicer/nope.stl").status_code == 404


def test_open_in_slicer_hands_only_the_built_file_to_orcaslicer(
    client, tmp_path, monkeypatch
):
    built = tmp_path / "box.stl"
    built.write_bytes(b"x")
    monkeypatch.setattr(main, "_last_build_files", {"box.stl": built})

    calls = []

    class Done:
        returncode = 0
        stderr = ""

    monkeypatch.setattr(
        main.subprocess, "run", lambda args, **kw: calls.append(args) or Done()
    )

    assert client.post("/open-in-slicer/box.stl").json() == {"success": True}
    assert calls == [["open", "-a", "OrcaSlicer", str(built)]]


# ------------------------------------------------------------
# Build + autosave
# ------------------------------------------------------------

def test_autosave_round_trip(client):
    assert client.get("/autosave").json() == {"content": None}

    assert client.post("/autosave", json={"script": "X = 1\n"}).json() == {"success": True}
    assert client.get("/autosave").json() == {"content": "X = 1\n"}

    client.delete("/autosave")
    assert client.get("/autosave").json() == {"content": None}


def test_build_endpoint_reports_files_and_whitelists_them(client, tmp_path, monkeypatch):
    # main and the executor each hold a reference to the workspace; point
    # both at the temp dir so the test never writes into the real one.
    monkeypatch.setattr(executor, "WORKSPACE", tmp_path)

    response = client.post(
        "/build", json={"script": 'open("ep_test.stl", "w").write("solid")'}
    )
    body = response.json()

    assert body["success"] is True
    assert "ep_test.stl" in body["files"]
    assert client.get("/model/ep_test.stl").status_code == 200
