import asyncio

from wsrpc_aiohttp import WSRPCClient


async def sleep(socket):
    await asyncio.sleep(2)
    print("bar")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    async def main():
        client = WSRPCClient("ws://127.0.0.1:8000/ws/", loop=loop)
        client.add_route("test", sleep)

        await client.connect()

        print(await client.call("test"))

        await client.close()

    loop.run_until_complete(main())
