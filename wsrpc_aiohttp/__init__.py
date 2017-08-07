import os.path
from .websocket.handler import WebSocketRoute, WebSocketAsync, WebSocketThreaded
from .websocket.route import decorators
from wsrpc_aiohttp.websocket.client import WSRPCClient


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')


__all__ = (
    'decorators',
    'STATIC_DIR',
    'WebSocketAsync',
    'WebSocketRoute',
    'WebSocketThreaded',
    'WSRPCClient',
)
