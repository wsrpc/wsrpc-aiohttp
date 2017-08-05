import os.path
from .websocket import WebSocketRoute, WebSocket, WebSocketThreaded
from .websocket.route import decorators
from wsrpc_aiohttp.websocket.client import WSRPCClient


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
