import uuid

from wsrpc_aiohttp.testing import BaseTestCase, async_timeout
from wsrpc_aiohttp import WebSocketRoute


class ReverseRoute(WebSocketRoute):
    def init(self, data):
        self.data = data

    def reverse(self):
        self.data = self.data[::-1]

    def get_data(self):
        return self.data


class TestServerRPC(BaseTestCase):
    @async_timeout
    async def test_call(self):
        self.WebSocketHandler.add_route('reverse', ReverseRoute)

        client = await self.get_ws_client()

        data = str(uuid.uuid4())

        await client.proxy.reverse(data=data)
        await client.proxy.reverse.reverse()

        response = await client.proxy.reverse.get_data()

        self.assertEqual(response, data[::-1])
