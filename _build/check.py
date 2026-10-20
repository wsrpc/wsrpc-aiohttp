"""Verify that wheel and sdist contain the complete client snapshot."""

import hashlib
import json
import sys
import tarfile
import zipfile
from pathlib import Path

from .client import ROOT


def check(directory: Path) -> None:
    lock = json.loads((ROOT / "_build/client.json").read_text())
    wheels = list(directory.glob("*.whl"))
    sources = list(directory.glob("*.tar.gz"))
    if not wheels or not sources:
        raise ValueError("Build both wheel and sdist before checking artifacts")
    for path in wheels:
        with zipfile.ZipFile(path) as wheel:
            for name, digest in lock["files"].items():
                data = wheel.read(f"{lock['module']}/static/{name}")
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError(f"Client asset mismatch: {path}: {name}")
    for path in sources:
        with tarfile.open(path) as source:
            prefix = source.getnames()[0].split("/")[0]
            for name, digest in lock["files"].items():
                stream = source.extractfile(
                    f"{prefix}/{lock['module']}/static/{name}"
                )
                assert stream is not None
                if hashlib.sha256(stream.read()).hexdigest() != digest:
                    raise ValueError(f"Client asset mismatch: {path}: {name}")
            for name in (
                "backend.py",
                "client.py",
                "client.json",
                "sdist-client",
            ):
                source.getmember(f"{prefix}/_build/{name}")
    print("Wheel and sdist contain the verified wsrpc-ts client snapshot")


if __name__ == "__main__":
    check(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist")
