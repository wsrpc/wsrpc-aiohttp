import subprocess
from contextlib import chdir
from pathlib import Path

import requests


def download(url: str, dest: Path):
    print(f"Downloading {url}")
    response = requests.get(url)
    response.raise_for_status()
    with open(dest, "wb") as fp:
        for chunk in response.iter_content(chunk_size=65535):
            fp.write(chunk)

def docs():
    docs = Path("docs")
    plantuml = (Path("contrib") / "plantuml.jar").resolve()

    def plantuml_render(*filenames):
        with chdir(str(docs / "source")):
            subprocess.run(
                ["java", "-jar", str(plantuml), "-tsvg",
                "-quiet", "-progress", "-overwrite", "-nometadata",
                "-o", "_static", *filenames]
            )

    plantuml_render("*.puml")

    with chdir(str(docs)):
        subprocess.run(["poetry", "run", "sphinx-build", "source", "build"])



def build(*args, **kwargs):
    base_url = "https://unpkg.com/@wsrpc/client"
    files = "wsrpc.d.ts", "wsrpc.es6.js"
    dist_files = "wsrpc.js", "wsrpc.min.js", "wsrpc.min.js.map"

    dest_path = Path("wsrpc_aiohttp") / "static"

    for fname in files:
        download(f'{base_url}/{fname}', dest_path / fname)

    for fname in dist_files:
        download(f'{base_url}/dist/{fname}', dest_path / fname)
