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


@pytest.fixture
def application(handler, socket_path):
    app = Application()
    app.router.add_route("*", socket_path, handler)
    return app


@pytest.fixture
async def session(aiohttp_client, application, loop) -> ClientSession:
    return await aiohttp_client(application)


@pytest.fixture
async def client(session: ClientSession, socket_path, loop) -> WSRPCClient:
    return WSRPCClient(socket_path, session=session, loop=loop)
