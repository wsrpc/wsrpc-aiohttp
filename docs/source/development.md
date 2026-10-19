# Development and releases

## Environment

Install [uv](https://docs.astral.sh/uv/), then clone the repository and synchronize the locked environment:

```shell
git clone https://github.com/wsrpc/wsrpc-aiohttp.git
cd wsrpc-aiohttp
uv sync --locked
```

All tools for development, tests and documentation are in the `dev` dependency group. Python versions before 3.14 use pytask 0.5.8 because pytask 0.6 depends on msgspec, which does not support free-threaded 3.13. Newer Python versions use pytask 0.6; both run the same tasks. `uv.lock` records the resolved versions. Use `uv lock` after intentionally changing dependencies; use `uv sync --locked` to reproduce the existing environment.

## Tasks

[Pytask](https://pytask-dev.readthedocs.io/) runs the commands in `task_dev.py`:

```shell
uv run --locked pytask
```

Select individual tasks using `-k`. Checks run on every invocation rather than being skipped because of cached results.

| Selection | What it does |
| --- | --- |
| `-k lint` | Ruff linting and formatting checks for the whole repository |
| `-k typing` | mypy checks for the library, task runner and consumer type contracts |
| `-k tests` | pytest, Markdown examples and coverage reports |
| `-k test_docs` | Only the marked examples in README and documentation |
| `-k 'docs and not test_docs'` | Sphinx HTML with warnings treated as errors |
| `-k build` | Source distribution and wheel through `uv build` |

The root `Makefile` provides aliases for these tasks. On Windows, use the `uv run ...` commands directly.

Tests normally use the standard JSON codec. To exercise a third-party codec through the public `loads`/`dumps` extension points on regular CPython:

```shell
uv run --locked --group serializers pytask -k tests
```

This test group contains orjson. It is not required by the library or by free-threaded tests. The optional `uvloop` group is available for local experiments; the standard test matrix uses asyncio.

## Python support

CI tests CPython 3.10–3.15 and free-threaded CPython 3.13–3.15 on Linux. It also tests CPython 3.14 on Windows and macOS. Free-threaded jobs verify that the interpreter is built without the GIL and that importing dependencies and running the test suite leave the GIL disabled.

To select an interpreter locally:

```shell
uv run --locked --python 3.10 pytask -k tests
uv run --locked --python 3.15t pytask -k tests
```

To include the GIL checks used in CI, set `WSRPC_EXPECT_FREE_THREADED=1` when running the free-threaded suite. The tests include simultaneous synchronous handlers running in separate threads.

## Documentation

Pages in `docs/source` use MyST Markdown. Sphinx builds them with the Furo theme; the API reference uses autodoc. Python docstrings remain in Sphinx's reStructuredText format and are evaluated through MyST's `eval-rst` bridge.

Build and open `docs/build/html/index.html`:

```shell
uv run --locked pytask -k 'docs and not test_docs'
```

Read the Docs uses the same task. When `READTHEDOCS_OUTPUT` is set, the task writes HTML to its `html` subdirectory.

To turn a self-contained Python code block into a documentation test, place an HTML comment immediately above it:

````markdown
<!-- name: test_example -->
```python
assert 2 + 2 == 4
```
````

Each marked block must include its own setup. Use an ephemeral local server for network examples and close clients with a context manager. Run `uv run --locked pytask -k test_docs` to check them.

The quick-start Python and browser files live in `docs/source/examples/main`. The additional demo in `docs/source/examples` demonstrates stateful routes, callbacks and binary messages.

## Build distributions

```shell
uv run --locked pytask -k build
```

Artifacts are written to `dist/`. Both distributions include `py.typed` and the JavaScript client under `wsrpc_aiohttp/static`. The JavaScript files are vendored with their upstream version and license; building a package does not fetch them from the network. Generated documentation is excluded from the source distribution.

## Publish a release

The `publish.yml` workflow runs when a GitHub Release is **published**. Its build job checks out the release tag, strips an optional leading `v`, applies that version with `uv version`, and builds the distributions. For example, both `4.1.0` and `v4.1.0` produce package version `4.1.0`; prerelease tags such as `v4.1.0rc1` are also accepted.

The publish job uploads the artifacts to PyPI using Trusted Publishing, then attaches the source distribution and wheel to the GitHub Release. The version change is made in the build checkout; the workflow does not commit it back to the branch or move the tag.

Before the first automated release, configure a [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/) for the existing `wsrpc-aiohttp` project:

| Setting | Value |
| --- | --- |
| Repository owner | `wsrpc` |
| Repository name | `wsrpc-aiohttp` |
| Workflow filename | `publish.yml` |
| GitHub environment | `pypi` |

The workflow uses the GitHub environment `pypi`; its protection rules can control who approves publishing. An API token is not needed for this flow. After the desired revision passes CI, create and publish a GitHub Release with its version tag to start the workflow.
