# Quick start

This example exposes a `uuid4` method, serves the bundled JavaScript client, and provides both Python and browser clients.

## Run the server

From the repository root, install the development environment and start the example:

```shell
uv sync --locked
uv run --locked python docs/source/examples/main/server.py
```

The server listens on `http://127.0.0.1:8000`. Its static directory is resolved relative to the script, so the command works from the repository root.

```{literalinclude} examples/main/server.py
:language: python
```

`Socket` is a dedicated handler class. Registering its routes keeps them separate from applications using another handler class. Each exposed function receives the current connection as its first argument.

## Call from Python

In another terminal:

```shell
uv run --locked python docs/source/examples/main/client.py
```

```{literalinclude} examples/main/client.py
:language: python
```

The context manager connects the client on entry and closes the connection and its HTTP session on exit. Create clients inside an asynchronous function and start it with `asyncio.run()`.

## Call from a browser

Open <http://127.0.0.1:8000/web-client.html> and click **Generate UUID**.

```{literalinclude} examples/main/web-client.html
:language: html
```

The page constructs a WebSocket URL from its own origin, selecting `ws://` for HTTP and `wss://` for HTTPS. The script is served at `/js/wsrpc.min.js` from the installed Python package.

## Test a complete round trip

For tests or scripts that need a temporary server, `aiohttp.test_utils.TestServer` selects an available local port. This example is executed by markdown-pytest:

<!-- name: test_websocket_round_trip -->
```python
import asyncio
from aiohttp import web
from aiohttp.test_utils import TestServer
from wsrpc_aiohttp import WebSocketAsync, WSRPCClient


async def main() -> None:
    class Socket(WebSocketAsync):
        pass

    async def multiply(socket: Socket, *, x: int, y: int) -> int:
        return x * y

    Socket.add_route("multiply", multiply)
    app = web.Application()
    app.router.add_get("/ws/", Socket)
    async with TestServer(app) as server:
        async with WSRPCClient(str(server.make_url("/ws/"))) as client:
            assert await client.proxy.multiply(x=6, y=7) == 42


asyncio.run(main())
```

## Message flow

Either side can initiate a call while earlier calls are still running. Responses carry the request identifier, so they can arrive in a different order from the requests.

```{image} _static/explanation.svg
:alt: Request and response flow between a WebSocket server and client
```
