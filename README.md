# WSRPC aiohttp

[![Github Actions](https://github.com/wsrpc/wsrpc-aiohttp/workflows/tests/badge.svg)](https://github.com/wsrpc/wsrpc-aiohttp/actions?query=branch%3Amaster)


[![Latest Version](https://img.shields.io/pypi/v/wsrpc-aiohttp.svg)](https://pypi.python.org/pypi/wsrpc-aiohttp/)

[![python wheel](https://img.shields.io/pypi/wheel/wsrpc-aiohttp.svg)](https://pypi.python.org/pypi/wsrpc-aiohttp/)

[![Python Versions](https://img.shields.io/pypi/pyversions/wsrpc-aiohttp.svg)](https://pypi.python.org/pypi/wsrpc-aiohttp/)

[![license](https://img.shields.io/pypi/l/wsrpc-aiohttp.svg)](https://pypi.python.org/pypi/wsrpc-aiohttp/)

Easy to use minimal WebSocket Remote Procedure Call library for aiohttp
servers.

See [online demo](https://demo.wsrpc.info/) and
[documentation](https://docs.wsrpc.info/) with examples.

## Features

-   Call server functions from the client side;
-   Call client functions from the server (for example to notify clients
    about events);
-   Async connection protocol: both server or client are able to call
    several functions and get responses as soon as each response would
    be ready in any order.
-   Fully async server-side functions;
-   Transfer any exceptions from a client side to the server side and
    vise versa;
-   Ready-to-use frontend-library without dependencies;
-   Thread-based websocket handler for writing fully-synchronous backend
    code (for synchronous database drivers etc.)
-   Protected server-side methods (cliens are not able to call methods,
    starting with underline directly);
-   Signals for introspection

## Installation

Install via pip:

    pip install wsrpc-aiohttp

Python 3.10 or newer is required, including free-threaded CPython 3.13–3.15. Messages use the standard library JSON codec. You can supply custom `loads` and `dumps` callbacks to `WSRPCClient` or `WebSocketAsync.configure()`. A custom `dumps` callback must return `str` and accept a `default` serializer keyword argument.

Python module provides client js library out of the box. But for pure
javascript applications you can install [standalone js client
library](https://www.npmjs.com/package/@wsrpc/client) using npm:

    npm install @wsrpc/client

## Usage

Backend code:

<!-- name: test_backend_configuration -->
```python
import logging
from time import time

import aiohttp.web
from wsrpc_aiohttp import Route, STATIC_DIR, WebSocketAsync, decorators


log = logging.getLogger(__name__)


# This class can be called by client.
# Connection object will have this class instance after calling route-alias.
class TestRoute(Route):
    # This method will be executed when client calls route-alias
    # for the first time.
    def init(self, **kwargs):
        # Python __init__ must be return "self".
        # This method might return anything.
        return kwargs

    # This method named by camelCase because the client can call it.
    @decorators.proxy
    async def getEpoch(self):

        # You can execute functions on the client side
        await self.do_notify()

        return time()

    # This method calls function on the client side
    @decorators.proxy
    async def do_notify(self):
        awesome = "Somebody executed test1.getEpoch method!"
        await self.socket.call("notify", result=awesome)


app = aiohttp.web.Application()
app.router.add_route("*", "/ws/", WebSocketAsync)  # Websocket route
app.router.add_static("/js", STATIC_DIR)  # WSRPC js library
app.router.add_static("/", ".")  # Your static files

# Stateful request
# This is the route alias TestRoute as "test1"
WebSocketAsync.add_route("test1", TestRoute)

# Stateless request
WebSocketAsync.add_route("test2", lambda *a, **kw: True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    aiohttp.web.run_app(app, port=8000)
```

Frontend code:

``` HTML
<script type="text/javascript" src="/js/wsrpc.min.js"></script>
<script>
    var url = (window.location.protocol==="https:"?"wss://":"ws://") + window.location.host + '/ws/';
    RPC = new WSRPC(url, 8000);

    // Configure client API, that can be called from server
    RPC.addRoute('notify', function (data) {
        console.log('Server called client route "notify":', data);
        return data.result;
    });
    RPC.connect();

    // Call stateful route
    // After you call that route, server would execute 'notify' route on the
    // client, that is registered above.
    RPC.call('test1.getEpoch').then(function (data) {
        console.log('Result for calling server route "test1.getEpoch": ', data);
    }, function (error) {
        alert(error);
    });

    // Call stateless method
    RPC.call('test2').then(function (data) {
        console.log('Result for calling server route "test2"', data);
    });
</script>
```

## Development

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync --locked
uv run --locked pytask         # all checks, docs and distributions
uv run --locked pytask -k tests # pytest, including Markdown examples
uv run --locked pytask -k lint  # Ruff checks and formatting
```

The documentation is built into `docs/build/html`. To run only the Markdown examples, use `uv run --locked pytask -k test_docs`.

## Versioning

This software follows [Semantic Versioning](http://semver.org/)
