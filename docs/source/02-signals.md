# Signals

Signals run asynchronous callbacks when connections change state or a handler starts, succeeds or fails. Connect callbacks before serving requests. Callbacks must be coroutine functions; they run sequentially, and a callback exception is logged without stopping the remaining callbacks.

## Available signals

Connection signals belong to the WebSocket handler class. Their `socket` argument is the underlying aiohttp `WebSocketResponse`, and `request` is the incoming aiohttp request.

| Signal | Keyword arguments | When it runs |
| --- | --- | --- |
| `ON_CONN_OPEN` | `socket`, `request` | Before authorization and the WebSocket upgrade |
| `ON_AUTH_SUCCESS` | `socket`, `request` | After `authorize()` returns true, before the upgrade |
| `ON_AUTH_FAIL` | `socket`, `request` | After `authorize()` returns false |
| `ON_CONN_FAIL` | `socket`, `request`, `err` | If preparing the WebSocket response raises an exception |
| `ON_CONN_CLOSE` | `socket`, `request` | When handling an established connection finishes, before cleanup |

Call signals are available on both server and Python client connections:

| Signal | Keyword arguments | When it runs |
| --- | --- | --- |
| `ON_CALL_START` | `method`, `serial`, `args`, `kwargs` | Before resolving and executing a received call |
| `ON_CALL_SUCCESS` | `method`, `serial`, `args`, `kwargs`, `result` | After the handler returns, before sending the result |
| `ON_CALL_FAIL` | `method`, `serial`, `args`, `kwargs`, `err` | If executing the handler raises an exception |

`ON_CALL_FAIL` describes exceptions from the handler body. A failure to resolve a route still returns an RPC error, but does not reach this signal.

## Measure handler duration

This example uses a `ContextVar` so concurrent calls keep separate start times. Signals are class attributes: subclasses inherit the same signal objects unless they replace them. Define fresh signals when an application needs independent subscriptions.

<!-- name: example_02_signals_1 -->
```python
import logging
from contextvars import ContextVar
from time import monotonic
from wsrpc_aiohttp import WebSocketAsync
from wsrpc_aiohttp.signal import Signal

log = logging.getLogger(__name__)
started_at: ContextVar[float] = ContextVar("started_at")


class Socket(WebSocketAsync):
    ON_CALL_START: Signal[...] = Signal()
    ON_CALL_SUCCESS: Signal[...] = Signal()
    ON_CALL_FAIL: Signal[...] = Signal()


async def on_start(method: str, **kwargs) -> None:
    started_at.set(monotonic())


async def on_finish(method: str, **kwargs) -> None:
    log.info("%s took %.3fs", method, monotonic() - started_at.get())


Socket.ON_CALL_START.connect(on_start)
Socket.ON_CALL_SUCCESS.connect(on_finish)
Socket.ON_CALL_FAIL.connect(on_finish)
```

The `args` and `kwargs` values describe the handler invocation. A successful function route receives the socket as its first positional argument; a bound route method already has its instance.

## Typed standalone signals

`Signal` is generic over its callback parameters. The following example is executed as part of the documentation tests:

<!-- name: test_typed_signal -->
```python
import asyncio
from wsrpc_aiohttp.signal import Signal


async def main() -> None:
    messages: list[str] = []
    signal: Signal[[str]] = Signal()

    async def receive(message: str) -> None:
        messages.append(message)

    signal.connect(receive)
    await signal.call("connected")
    assert messages == ["connected"]

    signal.freeze()
    assert signal.is_frozen
    copy = signal.copy()
    assert not copy.is_frozen
    await copy.call("copied")
    assert messages == ["connected", "copied"]


asyncio.run(main())
```

`freeze()` prevents further subscriptions. `copy()` preserves existing receivers and returns an unfrozen signal. `Socket.freeze()` freezes all of that handler's connection and call signals.
