import asyncio

from wsrpc_aiohttp import WSRPCClient


async def main(endpoint: str = "http://127.0.0.1:8000/ws/") -> None:
    async with WSRPCClient(endpoint) as client:
        print(await client.proxy.uuid4())


if __name__ == "__main__":
    asyncio.run(main())
