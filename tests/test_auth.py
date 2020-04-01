from http import HTTPStatus

import pytest
from aiohttp import WSServerHandshakeError
from wsrpc_aiohttp import WebSocketAsync, WSRPCClient


class WebSocketHandler(WebSocketAsync):
    AUTHORIZE = False

    async def authorize(self):
        return self.AUTHORIZE


@pytest.fixture
def handler():
    return WebSocketHandler


async def test_auth_fail(client: WSRPCClient, handler):
    handler.AUTHORIZE = False

    with pytest.raises(WSServerHandshakeError) as e:
        await client.connect()

    assert e.value.status == HTTPStatus.FORBIDDEN


async def test_auth_ok(client: WSRPCClient, handler):
    handler.AUTHORIZE = True
    await client.connect()
