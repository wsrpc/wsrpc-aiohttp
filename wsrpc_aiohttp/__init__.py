from pathlib import Path

from .websocket import decorators
from .websocket.client import WSRPCClient
from .websocket.common import ClientException, WSRPCBase, WSRPCError
from .websocket.handler import WebSocketAsync, WebSocketBase, WebSocketThreaded
from .websocket.route import AllowedRoute, PrefixRoute, Route, WebSocketRoute
from .websocket.tools import serializer

STATIC_DIR = str(Path(__file__).parent.resolve() / "static")


__all__ = (
    "AllowedRoute",
    "ClientException",
    "PrefixRoute",
    "Route",
    "STATIC_DIR",
    "WSRPCBase",
    "WSRPCClient",
    "WSRPCError",
    "WebSocketAsync",
    "WebSocketBase",
    "WebSocketRoute",
    "WebSocketThreaded",
    "decorators",
    "serializer",
)
