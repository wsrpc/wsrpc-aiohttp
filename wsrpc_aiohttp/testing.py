import asyncio
import os
from functools import partial, wraps

import aiohttp.web
from asynctest import TestCase
from aiohttp.test_utils import TestClient, TestServer
from yarl import URL

from .websocket.handler import WebSocketAsync
from .websocket.client import WSRPCClient


try:
    DEFAULT_TIMEOUT = int(os.getenv('ASYNC_TIMEOUT', '5'))
except:
    DEFAULT_TIMEOUT = 5


def async_timeout(func=None, seconds=DEFAULT_TIMEOUT):
    """ Add timeout to a coroutine function and return it.

    .. code-block: python

        class TimedOutTestCase(TestCase):
            @async_timeout
            async def test_default_timeout(self):
                await asyncio.sleep(999, loop=self.loop)

            @async_timeout(seconds=1)
            async def test_custom_timeout(self):
                await asyncio.sleep(999, loop=self.loop)

    :param func: Coroutine function
    :param seconds: optional time limit in seconds. Default is 10.
    :type seconds: int
    :raises: TimeoutError if time limit is reached

    .. note::
        Default timeout might be set as ``ASYNC_TIMEOUT`` environment variable.

    """
    if func is None:
        return partial(async_timeout, seconds=seconds)

    # convert function to coroutine anyway
    coro_func = asyncio.coroutine(func)

    @wraps(func)
    async def wrap(self: TestCase, *args, **kwargs):
        task = self.loop.create_task(
            coro_func(self, *args, **kwargs)
        )  # type: asyncio.Task

        cancelled = False

        def on_timeout(task: asyncio.Task, loop: asyncio.AbstractEventLoop):
            nonlocal cancelled

            if task.done():
                return

            task.cancel()
            cancelled = True

        handle = self.loop.call_later(seconds, on_timeout, task, self.loop)
        task.add_done_callback(lambda x: handle.cancel())

        try:
            return await task
        except asyncio.CancelledError as e:
            if cancelled:
                raise TimeoutError from e
            raise

    return wrap


class BaseTestCase(TestCase):
    WebSocketHandler = WebSocketAsync

    async def get_application(self):
        app = aiohttp.web.Application()
        self.path = '/ws/'
        app.router.add_route('*', self.path, self.WebSocketHandler)
        return TestServer(app)

    async def get_ws_client(self, timeout=None) -> WSRPCClient:
        ws_client = WSRPCClient(endpoint=self.url, timeout=timeout)
        await ws_client.connect()
        self.addCleanup(ws_client.close)
        return ws_client

    async def setUp(self):
        super(TestCase, self).setUp()
        asyncio.set_event_loop(self.loop)

        self.app = await self.get_application()
        self.http_client = TestClient(self.app, loop=self.loop)

        await self.http_client.start_server()
        self.addCleanup(self.http_client.server.close)

        self.url = URL.build(scheme="http", host=self.http_client.server.host,
                             port=self.http_client.server.port, path=self.path)
