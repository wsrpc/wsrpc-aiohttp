# Introduction

## Overview

Client perform connection to the server.
When connection is successfully initialized client or server might call
remote methods.

```{image} _static/server-client.svg

```

## Socket instance

Server or client has a similar interface based on
{py:class}`wsrpc_aiohttp.WSRPCBase`.

That's means the two sides has {py:func}`wsrpc_aiohttp.WSRPCBase.call` and
method {py:attr}`wsrpc_aiohttp.WSRPCBase.proxy`

## Routes

It's an abstraction for exposing local functions to the remote side.
Route it's an alias for function.

### Function based routes

Lets write simple function:

```python
def multiply(socket, *, x, y):
    return x * y
```

Then register this function on the client side:

```python
client = WSRPCClient("ws://127.0.0.1:8000/ws/")
client.add_route("multiply", multiply)

await client.connect()
```

And create the function on the server side:

```python
async def multiply_loopback(socket: WebSocketAsync):
    return await socket.proxy.multiply(x=10, y=20)
```

Register to the server-side socket.

```python
WebSocketAsync.add_route("multiply_loopback", multiply_loopback)
```

### Class based routes

The `route` can be a based on class {py:class}`wsrpc_aiohttp.WebSocketRoute`.
In this case socket instance will store an initialized instance of
this class and instance appears after first route call.

```python
from wsrpc_aiohttp import Route, WebSocketAsync, decorators


class Storage(Route[WebSocketAsync]):
    async def init(self):
        """method which will be called after the first route call"""
        self._internal = dict()

    @decorators.proxy
    async def get(self, key, default=None):
        return self._internal.get(key, default)

    @decorators.proxy
    async def set(self, key, value):
        self._internal[key] = value
        return True


WebSocketAsync.add_route("kv", Storage)
```

Python client code:

```python
client = WSRPCClient("ws://127.0.0.1:8000/ws/")
await client.connect()

assert await client.proxy.kv.set(key="foo", value="bar")
# The `init` will be called on the server side before `set`

assert await client.proxy.kv.get(key="foo")
```

Javascript client code:

```javascript
RPC = new WSRPC("ws://127.0.0.1:8000/ws/");
RPC.connect();

RPC.call('kv.set', {'key': 'foo', 'value': 'bar'}).then(function (result) {
    console.log('Key foo was set');
}).then(function () {
    RPC.call('kv.get', {'key': 'foo'}).then(function (result) {
        console.log('Key foo is', result);
    });
});
```

## Client to server calls

Let's define another route on the server side for demonstrate simple case.

```python
async def subtract(socket: WebSocketAsync, *, a, b):
    return a - b


WebSocketAsync.add_route("subtract", subtract)
```

After server initialization any client can call it.

```python
client = WSRPCClient("ws://127.0.0.1:8000/ws/")
await client.connect()

assert await client.proxy.subtract(a=1, b=9) == -8
```

## Server to client calls

The {py:class}`wsrpc_aiohttp.WSRPCBase` instance will be passed to the route
function. That's means you can call function on the remote side inside
of route function.

Code of the server side:

```python
async def multiply_loopback(socket: WebSocketAsync):
    # multiply will be called on the client side
    return await socket.proxy.multiply(x=10, y=20)


...

WebSocketAsync.add_route("multiply_loopback", multiply_loopback)
```

The client-side code:

```python
def multiply(socket, *, x, y):
    return x * y


...

client = WSRPCClient("ws://127.0.0.1:8000/ws/")
client.add_route("multiply", multiply)
await client.connect()

await client.proxy.multiply_loopback()
```

The sequence diagram for this case:

```{image} _static/loopback-call.svg

```

