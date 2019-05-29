from wsrpc_aiohttp.testing import BaseTestCase, async_timeout
from wsrpc_aiohttp import WSRPCBase


async def emitter(socket: WSRPCBase):
    await socket.emit({"Hello": "world"})


class TestServerEvents(BaseTestCase):

    @async_timeout
    async def test_emitter(self):
        self.WebSocketHandler.add_route('emitter', emitter)
        client = await self.get_ws_client()

        future = self.loop.create_future()

        client.add_event_listener(future.set_result)

        await client.proxy.emitter()
        result = await future

        self.assertDictEqual(result, {"Hello": "world"})

