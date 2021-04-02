import asyncio

from wsrpc_aiohttp import WSRPCClient


async def test_frames_are_sent_in_correct_order(client: WSRPCClient):
    async with client:
        data = 'hello, world' * 1024
        coros = [
            client.call("ping", data=data)
            for _ in range(100)
        ]
        await asyncio.gather(*coros)
