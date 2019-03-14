from http import HTTPStatus

from aiohttp import WSServerHandshakeError

from wsrpc_aiohttp.testing import BaseTestCase
from wsrpc_aiohttp import WebSocketAsync


class TestAuth(BaseTestCase):
    class WebSocketHandler(WebSocketAsync):
        AUTHORIZE = False

        async def authorize(self):
            return self.AUTHORIZE

    async def test_auth_fail(self):
        self.WebSocketHandler.AUTHORIZE = False
        with self.assertRaises(WSServerHandshakeError) as e:
            await self.get_ws_client()

        self.assertEqual(e.exception.status, HTTPStatus.FORBIDDEN)

    async def test_auth_ok(self):
        self.WebSocketHandler.AUTHORIZE = True
        await self.get_ws_client()
