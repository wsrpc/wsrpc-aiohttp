"""Fetch byte-for-byte browser assets from a pinned @wsrpc/client release.

Update explicitly with ``python -m _build.client VERSION``. Normal builds use
the verified snapshot, including when building offline from an sdist.
"""

import base64
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path
from typing import Any
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "LICENSE": "package/LICENSE",
    "wsrpc.d.ts": "package/wsrpc.d.ts",
    "wsrpc.es6.js": "package/wsrpc.es6.js",
    "wsrpc.js": "package/dist/wsrpc.js",
    "wsrpc.js.map": "package/dist/wsrpc.js.map",
    "wsrpc.min.js": "package/dist/wsrpc.min.js",
    "wsrpc.min.js.map": "package/dist/wsrpc.min.js.map",
}


def download(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        return response.read()


def unpack(archive: bytes, lock: dict[str, Any]) -> dict[str, bytes]:
    digest = base64.b64encode(hashlib.sha512(archive).digest()).decode()
    if lock["integrity"] != f"sha512-{digest}":
        raise ValueError("@wsrpc/client archive integrity mismatch")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as source:
        # Read only known regular files; never extract archive paths to disk.
        for name, member_name in FILES.items():
            member = source.getmember(member_name)
            if not member.isfile():
                raise ValueError(f"Not a regular client asset: {member_name}")
            stream = source.extractfile(member)
            assert stream is not None
            files[name] = stream.read()
        metadata = source.extractfile("package/package.json")
        assert metadata is not None
        package = json.load(metadata)
        if (package["name"], package["version"]) != (
            "@wsrpc/client",
            lock["version"],
        ):
            raise ValueError("Unexpected @wsrpc/client package identity")
    return files


def hashes(files: dict[str, bytes]) -> dict[str, str]:
    return {
        name: hashlib.sha256(data).hexdigest() for name, data in files.items()
    }


def write_assets(
    root: Path, lock: dict[str, Any], files: dict[str, bytes]
) -> None:
    target = root / lock["module"] / "static"
    target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (target / name).write_bytes(data)


def ensure_client(root: Path = ROOT) -> None:
    lock = json.loads((root / "_build/client.json").read_text())
    target = root / lock["module"] / "static"
    if set(lock["files"]) != set(FILES):
        raise ValueError("Client lock must list every bundled asset")
    if all(
        (target / name).is_file()
        and hashlib.sha256((target / name).read_bytes()).hexdigest() == digest
        for name, digest in lock["files"].items()
    ):
        return
    files = unpack(download(lock["url"]), lock)
    if hashes(files) != lock["files"]:
        raise ValueError("@wsrpc/client asset checksums do not match the lock")
    write_assets(root, lock, files)


def update(version: str, root: Path = ROOT) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError("Specify an explicit npm release version")
    lock_path = root / "_build/client.json"
    lock = json.loads(lock_path.read_text())
    metadata = json.loads(
        download(f"https://registry.npmjs.org/@wsrpc/client/{version}")
    )
    lock.update(
        version=version,
        url=metadata["dist"]["tarball"],
        integrity=metadata["dist"]["integrity"],
    )
    files = unpack(download(lock["url"]), lock)
    lock["files"] = hashes(files)
    write_assets(root, lock, files)
    lock_path.write_text(json.dumps(lock, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m _build.client VERSION")
    update(sys.argv[1])
