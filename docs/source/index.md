# WSRPC aiohttp

[wsrpc-aiohttp](https://github.com/wsrpc/wsrpc-aiohttp) is a library for live web applications with two-way RPC over WebSockets.

## Features

- Call server functions from a Python or JavaScript client.
- Call client functions from the server, including during another RPC call.
- Run asynchronous handlers or synchronous handlers in a thread pool.
- Use functions or stateful route classes and protect private methods.
- Transfer results and errors asynchronously, in any order.
- Observe connections and procedure calls through signals.
- Serialize messages with standard JSON or custom codecs.
- Support regular and free-threaded CPython.

## Installation

Python 3.10 or newer is required.

```shell
pip install wsrpc-aiohttp
```

For JavaScript applications, the standalone client is available on npm:

```shell
npm install @wsrpc/client
```

The base installation supports free-threaded CPython 3.13–3.15. To use another codec, pass `loads` and `dumps` to `WSRPCClient` or `WebSocketAsync.configure()`. The `dumps` callback must return `str` and accept the `default` serializer keyword argument.

## Development

Install [uv](https://docs.astral.sh/uv/), then:

```shell
git clone https://github.com/wsrpc/wsrpc-aiohttp.git
cd wsrpc-aiohttp
uv sync --locked
make test
make linter
make typing
make docs
make build
```

`make test` also executes the marked Python examples in the Markdown documentation with markdown-pytest. `make docs` builds Sphinx HTML with MyST and Furo, treating warnings as errors. The HTML is written to `docs/build/html`.

## Contents

```{toctree}
:maxdepth: 3

00-quick-start
01-introduction
02-signals
apidoc
```

## Contributors

- [@mosquito](https://github.com/mosquito) (author)
