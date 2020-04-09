from wsrpc_aiohttp import WSRPCClient


async def test_ping(client: WSRPCClient):
    async with client:
        response = await client.call("ping", pong="pong")
        assert response["pong"], "pong"
