import asyncio

from wsrpc_aiohttp import WSRPCClient


async def main():
    client = WSRPCClient("ws://127.0.0.1:8000/ws/")

    await client.connect()
    print(await client.proxy.uuid4())
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
