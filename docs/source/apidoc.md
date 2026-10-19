# API reference

The public classes below are importable from `wsrpc_aiohttp`. See [routes and connections](01-introduction.md) for complete examples and [signals](02-signals.md) for lifecycle callback arguments.

## Connections, routes and serialization

`WSRPCClient` is the Python peer. `WebSocketAsync` and `WebSocketThreaded` are aiohttp handlers; both inherit connection configuration from `WebSocketBase`. `WSRPCBase` contains the shared RPC interface.

Route classes are generic over the socket type, for example `Route[WebSocketAsync]`. The `decorators` module controls which methods are exposed. `STATIC_DIR` is the installed directory containing the JavaScript client.

```{eval-rst}
.. automodule:: wsrpc_aiohttp
   :members: ClientException, WSRPCError, WSRPCBase, WSRPCClient, WebSocketBase, WebSocketAsync, WebSocketThreaded, Route, AllowedRoute, PrefixRoute, WebSocketRoute, serializer
   :imported-members:
```

## Method decorators

```{eval-rst}
.. automodule:: wsrpc_aiohttp.websocket.decorators
   :members: proxy, noproxy
```

## Signals

```{eval-rst}
.. automodule:: wsrpc_aiohttp.signal
   :members:
```

## Interfaces and helpers

The following modules define abstract connection interfaces and utility types used by the implementation. Applications normally use the public connection and route classes above.

```{eval-rst}
.. automodule:: wsrpc_aiohttp.websocket.abc
   :members: AbstractWebSocket, AbstractRoute, AbstractWSRPC, Proxy, ProxyMethod
```

```{eval-rst}
.. automodule:: wsrpc_aiohttp.websocket.tools
   :members: Lazy, awaitable
```
