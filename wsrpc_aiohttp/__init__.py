import os.path

from .websocket import decorators
from .websocket.client import WSRPCClient
from .websocket.handler import (
    ClientException,
    WebSocketAsync,
    WebSocketBase,
    WebSocketThreaded,
    WSRPCBase,
)
from .websocket.route import AllowedRoute, PrefixRoute, Route, WebSocketRoute
from .websocket.tools import serializer


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


__all__ = (
    "AllowedRoute",
    "ClientException",
    "PrefixRoute",
    "Route",
    "STATIC_DIR",
    "WSRPCBase",
    "WSRPCClient",
    "WebSocketAsync",
    "WebSocketBase",
    "WebSocketRoute",
    "WebSocketThreaded",
    "decorators",
    "serializer",
)
