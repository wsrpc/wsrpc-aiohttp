import asyncio

from wsrpc_aiohttp import WSRPCClient


async def joke(socket: WSRPCClient, *, joke: str) -> bool:
    print(joke)
    return True


async def main() -> None:
    client = WSRPCClient("http://127.0.0.1:8000/ws/")
    client.add_route("joke", joke)
    async with client:
        print(await client.proxy.test(message="Hello"))
        print(await client.proxy.test.getEpoch())
        print(await client.proxy.test.getJoke())


if __name__ == "__main__":
    asyncio.run(main())
