"""Build the current browser client directly from the wsrpc-ts repository."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "https://github.com/wsrpc/wsrpc-ts.git"
FILES = {
    "LICENSE": "packages/client/LICENSE",
    "wsrpc.d.ts": "packages/client/wsrpc.d.ts",
    "wsrpc.es6.js": "packages/client/wsrpc.es6.js",
    "wsrpc.js": "packages/client/dist/wsrpc.js",
    "wsrpc.js.map": "packages/client/dist/wsrpc.js.map",
    "wsrpc.min.js": "packages/client/dist/wsrpc.min.js",
    "wsrpc.min.js.map": "packages/client/dist/wsrpc.min.js.map",
}
ASSETS = {*FILES, "client-source.json"}


def run(*args: str, cwd: Path) -> str:
    executable = shutil.which(args[0])
    if executable is None:
        raise RuntimeError(f"Building the browser client requires {args[0]}")
    result = subprocess.run(
        [executable, *args[1:]],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    # Keep stdout available for PEP 517's return value; tool logs go to stderr.
    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")
    return result.stdout.strip()


def build(source: Path) -> None:
    run("npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund", cwd=source)
    run("node", "tools/build-client.mjs", cwd=source)


def update(
    root: Path = ROOT,
    ref: str | None = None,
    repository: str | None = None,
) -> None:
    repository = repository or REPOSITORY
    ref = ref or os.environ.get("WSRPC_CLIENT_REF", "HEAD")
    lock_path = root / "_build/client.json"
    module = json.loads(lock_path.read_text())["module"]
    with tempfile.TemporaryDirectory(prefix="wsrpc-client-") as temporary:
        source = Path(temporary)
        run("git", "init", "--quiet", cwd=source)
        run("git", "fetch", "--depth=1", "--", repository, ref, cwd=source)
        commit = run("git", "rev-parse", "FETCH_HEAD", cwd=source)
        run("git", "checkout", "--quiet", "--detach", commit, cwd=source)
        build(source)
        files = {
            name: (source / path).read_bytes() for name, path in FILES.items()
        }
        provenance = {
            "repository": repository,
            "ref": ref,
            "commit": commit,
            "package_lock_sha256": hashlib.sha256(
                (source / "package-lock.json").read_bytes()
            ).hexdigest(),
        }
        files["client-source.json"] = (
            json.dumps(provenance, indent=2) + "\n"
        ).encode()
    # Do not touch the previous snapshot until the whole client build succeeds.
    target = root / module / "static"
    target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (target / name).write_bytes(data)
    lock = {
        "module": module,
        **provenance,
        "files": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in files.items()
        },
    }
    lock_path.write_text(json.dumps(lock, indent=2) + "\n")


def verified(root: Path = ROOT) -> bool:
    lock = json.loads((root / "_build/client.json").read_text())
    target = root / lock["module"] / "static"
    return set(lock["files"]) == ASSETS and all(
        (target / name).is_file()
        and hashlib.sha256((target / name).read_bytes()).hexdigest() == digest
        for name, digest in lock["files"].items()
    )


def ensure_client(root: Path = ROOT, *, fresh: bool = False) -> None:
    marker = root / "_build/sdist-client"
    if marker.exists():
        expected = hashlib.sha256(
            (root / "_build/client.json").read_bytes()
        ).hexdigest()
        if marker.read_text() != expected or not verified(root):
            raise ValueError("The sdist browser client snapshot is corrupted")
    elif fresh or not verified(root):
        update(root)


@contextmanager
def freeze_snapshot(root: Path = ROOT):
    marker = root / "_build/sdist-client"
    created = not marker.exists()
    if created:
        marker.write_text(
            hashlib.sha256(
                (root / "_build/client.json").read_bytes()
            ).hexdigest()
        )
    try:
        yield
    finally:
        if created:
            marker.unlink()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit("Usage: python -m _build.client [GIT_REF]")
    update(ref=sys.argv[1] if len(sys.argv) == 2 else None)
