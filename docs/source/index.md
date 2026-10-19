# WSRPC aiohttp

WSRPC provides two-way remote procedure calls over WebSockets for [aiohttp](https://docs.aiohttp.org/). Both peers can expose methods, make concurrent calls and receive results or remote exceptions over one connection.

Use functions for simple endpoints, route classes for state attached to a connection, and asynchronous signals to observe calls and connections. Python and JavaScript clients share the same RPC interface.

Python **3.10–3.15** is tested, including **free-threaded 3.13–3.15**. The base installation uses standard-library JSON and has no dependency on a native JSON extension.

## Install

```shell
pip install wsrpc-aiohttp
```

The wheel includes the JavaScript client served through `wsrpc_aiohttp.STATIC_DIR`. For a separate frontend project:

```shell
npm install @wsrpc/client
```

Start with the [quick start](00-quick-start.md), then read about [routes and connections](01-introduction.md).

```{toctree}
:maxdepth: 2

00-quick-start
01-introduction
02-signals
development
apidoc
```

Source code and issue tracker: [wsrpc/wsrpc-aiohttp](https://github.com/wsrpc/wsrpc-aiohttp). Created by [Dmitry Orlov](https://github.com/mosquito). The Python library is licensed under Apache-2.0; the bundled JavaScript client is licensed under MIT.
