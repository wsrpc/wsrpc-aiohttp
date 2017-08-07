from wsrpc_aiohttp.testing import BaseTestCase


class TestPing(BaseTestCase):
    async def test_ping(self):
        client = await self.get_ws_client()
        response = await client.call('ping', pong='pong')
        self.assertEqual(response['pong'], 'pong')
