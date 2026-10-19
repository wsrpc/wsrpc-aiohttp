import json
import os
import sys
import sysconfig

import pytest
from aiohttp import ClientSession
from aiohttp.web import Application

from wsrpc_aiohttp import WebSocketAsync, WSRPCClient

try:
    import orjson
except ImportError:
    orjson = None

CODECS = [
    pytest.param({}, id="default"),
    pytest.param(dict(loads=json.loads, dumps=json.dumps), id="json"),
]
if orjson is not None:
    CODECS.append(
        pytest.param(
            dict(
                loads=orjson.loads,
                dumps=lambda x, **kw: orjson.dumps(x, **kw).decode(),
            ),
            id="orjson",
        )
    )


@pytest.fixture
def handler():
    return WebSocketAsync


@pytest.fixture
def socket_path():
    return "/ws/"


@pytest.fixture(params=CODECS)
def application(request, handler, socket_path):
    app = Application()
    handler.configure(**request.param)
    app.router.add_route("*", socket_path, handler)
    return app


@pytest.fixture
async def session(aiohttp_client, application) -> ClientSession:
    return await aiohttp_client(application)


@pytest.fixture(params=CODECS)
async def client(request, session: ClientSession, socket_path) -> WSRPCClient:
    return WSRPCClient(socket_path, session=session, **request.param)


@pytest.fixture(scope="session", autouse=True)
def verify_free_threaded_runtime():
    if os.environ.get("WSRPC_EXPECT_FREE_THREADED") != "1":
        yield
        return
    assert sysconfig.get_config_var("Py_GIL_DISABLED") == 1
    assert not sys._is_gil_enabled()
    yield
    assert not sys._is_gil_enabled()
