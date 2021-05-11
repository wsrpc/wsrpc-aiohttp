# WSRPC aiohttp

[![Tests](https://github.com/wsrpc/wsrpc-aiohttp/actions/workflows/tests.yml/badge.svg)](https://github.com/wsrpc/wsrpc-aiohttp/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/wsrpc-aiohttp.svg)](https://pypi.org/project/wsrpc-aiohttp/)
[![Python versions](https://img.shields.io/pypi/pyversions/wsrpc-aiohttp.svg)](https://pypi.org/project/wsrpc-aiohttp/)
[![License](https://img.shields.io/pypi/l/wsrpc-aiohttp.svg)](LICENSE)

Two-way remote procedure calls over WebSockets for [aiohttp](https://docs.aiohttp.org/). A Python or JavaScript client can call the server, and the server can call the client over the same connection.

- Expose functions or stateful route classes.
- Run asynchronous handlers or synchronous handlers in a thread pool.
- Make concurrent calls and receive results independently.
- Receive remote errors as exceptions.
- Observe connection and call lifecycles with asynchronous signals.

Python **3.10–3.15** is tested, including **free-threaded 3.13–3.15**. See the [documentation](https://wsrpc.readthedocs.io/en/latest/) for routes, authentication, callbacks, signals and API reference.

## Install

```shell
pip install wsrpc-aiohttp
```

The Python package includes the JavaScript client. For a standalone frontend, it is also available on npm:

```shell
npm install @wsrpc/client
```

## Start a server

Save this as `server.py` and run `python server.py`:

<!-- name: test_readme_server -->
```python
from aiohttp import web
from wsrpc_aiohttp import STATIC_DIR, WebSocketAsync


class Socket(WebSocketAsync):
    pass


async def echo(socket: Socket, *, message: str) -> str:
    return message


def create_app() -> web.Application:
    Socket.add_route("echo", echo)
    app = web.Application()
    app.router.add_get("/ws/", Socket)
    app.router.add_static("/js/", STATIC_DIR)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="127.0.0.1", port=8000)
```

## Call it from Python

Save this as `client.py` and run it while the server is running:

<!-- name: example_README_2 -->
```python
import asyncio
from wsrpc_aiohttp import WSRPCClient


async def main() -> None:
    async with WSRPCClient("http://127.0.0.1:8000/ws/") as client:
        result = await client.proxy.echo(message="Hello from Python")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

Calls use keyword arguments. `await client.call("echo", message="Hello")` is equivalent to `await client.proxy.echo(message="Hello")`. The client context manager connects and closes the connection and its HTTP session.

The following self-contained test starts an ephemeral server and exercises the same API:

<!-- name: test_readme_round_trip -->
```python
import asyncio
from aiohttp import web
from aiohttp.test_utils import TestServer
from wsrpc_aiohttp import WebSocketAsync, WSRPCClient


async def round_trip() -> None:
    class Socket(WebSocketAsync):
        pass

    Socket.add_route("echo", lambda socket, *, message: message)
    app = web.Application()
    app.router.add_get("/ws/", Socket)
    async with TestServer(app) as server:
        async with WSRPCClient(str(server.make_url("/ws/"))) as client:
            assert await client.proxy.echo(message="Hello") == "Hello"


asyncio.run(round_trip())
```

## Call it from a browser

For a page served by the same application, load the bundled script from `/js/` and call the same method:

```html
<script src="/js/wsrpc.min.js"></script>
<script>
  const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = scheme + "//" + window.location.host + "/ws/";
  const rpc = new WSRPC(url);
  rpc.connect();
  rpc.call("echo", {message: "Hello from JavaScript"})
    .then(console.log)
    .catch(console.error);
</script>
```

The example selects `wss://` on HTTPS pages and `ws://` on HTTP pages. A complete browser example is in [the quick start](https://wsrpc.readthedocs.io/en/latest/00-quick-start.html).

## JSON codecs

Messages use the standard library `json` module. To use another codec, pass `loads` and `dumps` to `WSRPCClient` or `WebSocketAsync.configure()`. The `dumps` callback must return `str` and accept the `default` serializer keyword argument. The base installation works on free-threaded Python without a native JSON extension.

## Development

Install [uv](https://docs.astral.sh/uv/), clone the repository, then run:

```shell
uv sync --locked
uv run --locked pytask
```

All development dependencies are in `dev`. Pytask runs linting, type checking, tests (including marked Markdown examples), documentation and package builds. Select a task with `-k`:

```shell
uv run --locked pytask -k tests
uv run --locked pytask -k lint
uv run --locked pytask -k typing
uv run --locked pytask -k 'docs and not test_docs'
uv run --locked pytask -k build
```

Documentation is written in MyST Markdown, built by Sphinx with Furo, and written to `docs/build/html`. See [the development guide](https://wsrpc.readthedocs.io/en/latest/development.html) for the test matrix and release process.

## License and versioning

Licensed under [Apache-2.0](LICENSE). The bundled JavaScript client has its own [MIT license](wsrpc_aiohttp/static/LICENSE). Releases follow [Semantic Versioning](https://semver.org/).
