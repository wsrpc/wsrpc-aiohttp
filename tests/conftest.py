import json

import orjson
import pytest
from aiohttp import ClientSession
from aiohttp.web import Application

from wsrpc_aiohttp import WebSocketAsync, WSRPCClient


@pytest.fixture
def handler():
    return WebSocketAsync


@pytest.fixture
def socket_path():
    return "/ws/"


@pytest.fixture(
    params=[
        dict(loads=json.loads, dumps=json.dumps),
        dict(
            loads=orjson.loads,
            dumps=lambda x, **kw: orjson.dumps(x, **kw).decode(),
        ),
    ], ids=["json", "orjson"],
)
def application(request, handler, socket_path):
    app = Application()
    handler.configure(**request.param)
    app.router.add_route("*", socket_path, handler)
    return app


@pytest.fixture
async def session(aiohttp_client, application) -> ClientSession:
    return await aiohttp_client(application)


@pytest.fixture(
    params=[
        dict(loads=json.loads, dumps=json.dumps),
        dict(
            loads=orjson.loads,
            dumps=lambda x, **kw: orjson.dumps(x, **kw).decode(),
        ),
    ], ids=["json", "orjson"],
)
async def client(request, session: ClientSession, socket_path) -> WSRPCClient:
    return WSRPCClient(socket_path, session=session, **request.param)
