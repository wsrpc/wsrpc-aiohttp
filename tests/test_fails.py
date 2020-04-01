import pytest
from aiohttp import ClientConnectionError
from wsrpc_aiohttp import WSRPCClient


async def test_call_error(client: WSRPCClient, handler):
    class DataStore:
        def get_data(self, _):
            return 1000

    handler.add_route("get_data", DataStore().get_data)

    async with client:
        # Imitation of server connection has been closed
        client.socket._closed = True

        with pytest.raises(ClientConnectionError):
            await client.call("get_data")
