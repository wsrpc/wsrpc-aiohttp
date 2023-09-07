import logging
from pathlib import Path

import nox
import requests


def download(url: str, dest: Path):
    logging.info("Downloading %r", url)
    response = requests.get(url)
    response.raise_for_status()
    with open(dest, "wb") as fp:
        for chunk in response.iter_content(chunk_size=65535):
            fp.write(chunk)

@nox.session(python=False)
def tests(session: nox.Session):
    session.run("poetry", "run", "pytest", "--asyncio-mode=auto", "-v", "tests")

@nox.session(python=False)
def docs(session: nox.Session):
    docs = Path("docs")
    plantuml = (Path("contrib") / "plantuml.jar").resolve()

    def plantuml_render(*filenames):
        with session.chdir(str(docs / "source")):
            session.run(
                "java", "-jar", str(plantuml), "-tsvg",
                "-quiet", "-progress", "-overwrite", "-nometadata",
                "-o", "_static", *filenames, external=True,
            )

    plantuml_render("*.puml")

    with session.chdir(str(docs)):
        session.run("poetry", "run", "sphinx-build", "source", "build")


@nox.session(python=False)
def build(session: nox.Session):
    base_url = "https://unpkg.com/@wsrpc/client"
    files = "wsrpc.d.ts", "wsrpc.es6.js"
    dist_files = "wsrpc.js", "wsrpc.min.js", "wsrpc.min.js.map"

    dest_path = Path("wsrpc_aiohttp") / "static"

    for fname in files:
        download(f'{base_url}/{fname}', dest_path / fname)

    for fname in dist_files:
        download(f'{base_url}/dist/{fname}', dest_path / fname)
    session.run("poetry", "build")
