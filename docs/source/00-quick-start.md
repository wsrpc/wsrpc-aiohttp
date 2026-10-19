# Quick start

Let's try to write simple http server with WSRPC handler.

```{literalinclude} examples/main/server.py
:language: python
```

Next you have two options:

1. Browser WSRPC client.
2. Python WSRPC client.

## Browser client

```{literalinclude} examples/main/web-client.html
:language: html
```

You can try it on http://localhost:8000/web-client.html (required running server.py).

```{image} _static/web-client-demo.gif

```

## Python client

```{literalinclude} examples/main/client.py
:language: python
```

This is so useful for testing and shell scripts for your services.


## How it works

The following sequence diagram probably to explain some high level of the data-flow.

```{image} _static/explanation.svg

```


## A complete Python round trip

This example starts a local server, makes a real WebSocket call, and closes both sides. The ephemeral port makes it suitable for tests too.

<!-- name: test_websocket_round_trip -->
```python
import asyncio
from aiohttp import web
from aiohttp.test_utils import TestServer
from wsrpc_aiohttp import WebSocketAsync, WSRPCClient


async def main():
    class Socket(WebSocketAsync):
        pass

    async def multiply(socket, *, x, y):
        return x * y

    Socket.add_route("multiply", multiply)
    app = web.Application()
    app.router.add_get("/ws/", Socket)
    async with TestServer(app) as server:
        async with WSRPCClient(str(server.make_url("/ws/"))) as client:
            assert await client.proxy.multiply(x=6, y=7) == 42


asyncio.run(main())
```
