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

    @async_timeout
    async def test_call_func(self):
        def get_data(_):
            return 1000

        self.WebSocketHandler.add_route('get_data', get_data)

        client = await self.get_ws_client()

        response = await client.proxy.get_data()
        self.assertEqual(response, 1000)

    @async_timeout
    async def test_call_method(self):
        class DataStore:
            DATA = 1000

            def get_data(self, _):
                return 1000

        self.WebSocketHandler.add_route('get_data', DataStore().get_data)

        client = await self.get_ws_client()

        response = await client.proxy.get_data()
        self.assertEqual(response, 1000)
