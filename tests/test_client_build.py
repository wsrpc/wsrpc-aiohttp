"""Check upstream asset integrity and builds without npm access."""

import base64
import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from _build import client


@pytest.fixture
def upstream(tmp_path: Path):
    files = {name: name.encode() for name in client.FILES}
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        contents = {
            client.FILES[name]: data for name, data in files.items()
        } | {
            "package/package.json": json.dumps(
                {"name": "@wsrpc/client", "version": "4.5.1"}
            ).encode()
        }
        for name, data in contents.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    data = output.getvalue()
    lock = {
        "module": "example",
        "version": "4.5.1",
        "url": "https://registry.npmjs.org/locked-client.tgz",
        "integrity": "sha512-"
        + base64.b64encode(hashlib.sha512(data).digest()).decode(),
        "files": client.hashes(files),
    }
    (tmp_path / "_build").mkdir()
    (tmp_path / "_build/client.json").write_text(json.dumps(lock))
    return tmp_path, lock, files, data


def test_build_fetches_locked_client_and_repairs_stale_assets(
    upstream, monkeypatch: pytest.MonkeyPatch
):
    root, lock, files, archive = upstream
    calls = []

    def download(url):
        calls.append(url)
        return archive

    monkeypatch.setattr(client, "download", download)
    client.ensure_client(root)
    assert calls == [lock["url"]]
    target = root / "example/static"
    assert {p.name: p.read_bytes() for p in target.iterdir()} == files
    (target / "wsrpc.min.js").write_bytes(b"old client")
    client.ensure_client(root)
    assert (target / "wsrpc.min.js").read_bytes() == files["wsrpc.min.js"]
    assert calls == [lock["url"], lock["url"]]


@pytest.mark.parametrize("failure", ["archive", "asset", "version"])
def test_invalid_upstream_does_not_overwrite_snapshot(
    upstream, monkeypatch: pytest.MonkeyPatch, failure: str
):
    root, lock, files, archive = upstream
    client.write_assets(root, lock, files)
    old = root / "example/static/wsrpc.min.js"
    old.write_bytes(b"previous version")
    if failure == "archive":
        archive += b"corrupted"
    elif failure == "asset":
        lock["files"]["wsrpc.min.js"] = "wrong checksum"
    else:
        lock["version"] = "999.0.0"
    (root / "_build/client.json").write_text(json.dumps(lock))
    monkeypatch.setattr(client, "download", lambda url: archive)
    with pytest.raises(ValueError):
        client.ensure_client(root)
    assert old.read_bytes() == b"previous version"


def test_verified_snapshot_needs_no_network(
    upstream, monkeypatch: pytest.MonkeyPatch
):
    root, lock, files, _ = upstream
    client.write_assets(root, lock, files)

    def no_network(url):
        pytest.fail(f"Unexpected network request: {url}")

    monkeypatch.setattr(client, "download", no_network)
    client.ensure_client(root)
    client.ensure_client()  # Also verify the real, committed release snapshot.
