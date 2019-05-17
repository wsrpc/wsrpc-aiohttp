import asyncio
import uuid

import time

from wsrpc_aiohttp.testing import BaseTestCase, async_timeout
from wsrpc_aiohttp import WebSocketRoute


DATA_TO_RETURN = 1000


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
            return DATA_TO_RETURN

        self.WebSocketHandler.add_route('get_data', get_data)

        client = await self.get_ws_client()

        response = await client.proxy.get_data()
        self.assertEqual(response, DATA_TO_RETURN)

    @async_timeout
    async def test_call_method(self):
        class DataStore:
            def get_data(self, _):
                return DATA_TO_RETURN

        self.WebSocketHandler.add_route('get_data', DataStore().get_data)

        client = await self.get_ws_client()

        response = await client.proxy.get_data()
        self.assertEqual(response, DATA_TO_RETURN)

    @async_timeout
    async def test_call_timeout(self):

        def will_sleep_for(_, seconds):
            time.sleep(seconds)
            return DATA_TO_RETURN

        self.WebSocketHandler.add_route('will_sleep_for', will_sleep_for)

        client = await self.get_ws_client(timeout=2)

        response = await client.proxy.will_sleep_for(seconds=1)
        self.assertEqual(response, DATA_TO_RETURN)

        with self.assertRaises(asyncio.CancelledError):
            await client.proxy.will_sleep_for(seconds=7)
