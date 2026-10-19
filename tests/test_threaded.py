import asyncio
import threading

import pytest

from wsrpc_aiohttp import WebSocketThreaded


@pytest.fixture
def handler():
    return WebSocketThreaded


async def test_concurrent_threaded_calls(client, handler):
    barrier = threading.Barrier(2, timeout=5)
    loop_thread = threading.get_ident()

    def work(socket, *, value):
        barrier.wait()
        assert threading.get_ident() != loop_thread
        return value * 2

    handler.add_route("threaded_work", work)
    async with client:
        results = await asyncio.wait_for(
            asyncio.gather(
                client.proxy.threaded_work(value=10),
                client.proxy.threaded_work(value=20),
            ),
            timeout=10,
        )
        assert results == [20, 40]
