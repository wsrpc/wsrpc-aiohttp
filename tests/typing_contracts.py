"""Consumer contracts checked by mypy, including rejection of wrong types."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from wsrpc_aiohttp import Route, WebSocketAsync, WSRPCClient, decorators
from wsrpc_aiohttp.signal import Signal
from wsrpc_aiohttp.websocket.tools import Lazy, awaitable


class Socket(WebSocketAsync):
    label: str = "server"


class TypedRoute(Route[Socket]):
    @decorators.proxy
    def label(self) -> str:
        return self.socket.label


def render(value: int) -> str:
    return str(value)


async def render_async(value: int) -> str:
    return str(value)


async def receive(value: int) -> None:
    pass


if TYPE_CHECKING:
    lazy = Lazy(lambda: 42)
    number: int = lazy.func()
    wrong_lazy: str = lazy.func()  # type: ignore[assignment]

    sync_wrapper: Callable[[int], Awaitable[str]] = awaitable(render)
    async_wrapper: Callable[[int], Awaitable[str]] = awaitable(render_async)
    bad_wrapper: Callable[[str], Awaitable[str]] = awaitable(render)  # type: ignore[arg-type]

    decorated = decorators.proxy(render)
    result: str = decorated(42)
    decorated("wrong")  # type: ignore[arg-type]

    signal: Signal[[int]] = Signal()
    signal.connect(receive)
    signal.connect(render)  # type: ignore[arg-type]
    signal.call("wrong")  # type: ignore[arg-type, unused-coroutine]

    socket = Socket(None)
    route = TypedRoute(socket)
    typed_socket: Socket = route.socket
    bad_socket: WSRPCClient = route.socket  # type: ignore[assignment]
