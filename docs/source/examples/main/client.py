import asyncio

from wsrpc_aiohttp import WSRPCClient


loop = asyncio.get_event_loop()


async def main():
    client = WSRPCClient("ws://127.0.0.1:8000/ws/", loop=loop)

    await client.connect()
    print(await client.proxy.uuid4())
    await client.close()


if __name__ == "__main__":
    loop.run_until_complete(main())
