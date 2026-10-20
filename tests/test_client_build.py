"""Check Git updates and frozen sdist builds without network access."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from _build import client


def commit(repository: Path) -> str:
    client.run("git", "add", "--force", ".", cwd=repository)
    client.run(
        "git",
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "--quiet",
        "-m",
        "Update client",
        cwd=repository,
    )
    return client.run("git", "rev-parse", "HEAD", cwd=repository)


@pytest.fixture
def upstream(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repository = tmp_path / "upstream"
    repository.mkdir()
    client.run("git", "init", "--quiet", cwd=repository)
    for name, path in client.FILES.items():
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(name.encode())
    (repository / "package-lock.json").write_text("{}")
    first = commit(repository)
    root = tmp_path / "python"
    (root / "_build").mkdir(parents=True)
    (root / "_build/client.json").write_text(
        json.dumps({"module": "example", "files": {}})
    )
    monkeypatch.setattr(client, "REPOSITORY", str(repository))
    monkeypatch.setattr(client, "build", lambda source: None)
    return root, repository, first


def test_source_build_refreshes_current_git_head(upstream):
    root, repository, first = upstream
    client.ensure_client(root, fresh=True)
    assert client.verified(root)
    target = root / "example/static"
    assert (
        json.loads((target / "client-source.json").read_text())["commit"]
        == first
    )
    (repository / client.FILES["wsrpc.es6.js"]).write_bytes(b"new client")
    second = commit(repository)
    # A valid snapshot does not stop a source build from taking newer Git code.
    client.ensure_client(root, fresh=True)
    metadata = json.loads((target / "client-source.json").read_text())
    assert metadata["commit"] == second != first
    assert metadata["package_lock_sha256"] == hashlib.sha256(b"{}").hexdigest()
    assert (target / "wsrpc.es6.js").read_bytes() == b"new client"


def test_explicit_commit_reproduces_older_client(upstream):
    root, repository, first = upstream
    (repository / client.FILES["wsrpc.es6.js"]).write_bytes(b"new client")
    commit(repository)
    client.update(root, ref=first)
    assert (
        root / "example/static/wsrpc.es6.js"
    ).read_bytes() == b"wsrpc.es6.js"
    assert (
        json.loads((root / "_build/client.json").read_text())["commit"] == first
    )


def test_failed_upstream_build_preserves_previous_snapshot(
    upstream, monkeypatch: pytest.MonkeyPatch
):
    root, _, _ = upstream
    client.update(root)
    before = (root / "_build/client.json").read_bytes()

    def failed_build(source):
        raise subprocess.CalledProcessError(1, "npm ci")

    monkeypatch.setattr(client, "build", failed_build)
    with pytest.raises(subprocess.CalledProcessError):
        client.ensure_client(root, fresh=True)
    assert (root / "_build/client.json").read_bytes() == before
    assert client.verified(root)


def test_frozen_sdist_never_fetches_or_runs_node(
    upstream, monkeypatch: pytest.MonkeyPatch
):
    root, _, _ = upstream
    client.update(root)

    def forbidden(*args, **kwargs):
        pytest.fail("Frozen sdist attempted to rebuild the client")

    monkeypatch.setattr(client, "update", forbidden)
    with client.freeze_snapshot(root):
        client.ensure_client(root, fresh=True)
        (root / "example/static/wsrpc.js").write_bytes(b"corrupted")
        with pytest.raises(ValueError, match="corrupted"):
            client.ensure_client(root, fresh=True)
    assert not (root / "_build/sdist-client").exists()


def test_committed_snapshot_can_be_used_for_editable_install(
    monkeypatch: pytest.MonkeyPatch,
):
    def forbidden(*args, **kwargs):
        pytest.fail("Editable installation attempted to rebuild valid assets")

    monkeypatch.setattr(client, "update", forbidden)
    client.ensure_client()
    assert client.verified()
