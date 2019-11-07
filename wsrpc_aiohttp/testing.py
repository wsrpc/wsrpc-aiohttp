import asyncio
import os
import unittest.mock
from functools import partial, wraps

import aiohttp.web
import asynctest
from asynctest import TestCase
from aiohttp.test_utils import TestClient, TestServer
from yarl import URL

from wsrpc_aiohttp.websocket.common import awaitable
from .websocket.handler import WebSocketAsync
from .websocket.client import WSRPCClient


try:
    DEFAULT_TIMEOUT = int(os.getenv('ASYNC_TIMEOUT', '3'))
except Exception:
    DEFAULT_TIMEOUT = 3


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

    @wraps(func)
    async def wrap(*args, **kwargs):
        return await asyncio.wait_for(
            awaitable(func)(*args, **kwargs),
            timeout=seconds
        )

    return wrap


class AsyncTestCase(asynctest.TestCase):
    use_default_loop = False
    forbid_get_event_loop = True

    TEST_TIMEOUT = int(os.getenv('ASYNCIO_TEST_TIMEOUT', '30'))

    def _run_test_method(self, method):
        result = method()
        if asyncio.iscoroutine(result):
            self.loop.run_until_complete(
                asyncio.wait_for(result, timeout=self.TEST_TIMEOUT)
            )

    @property
    def _all_tasks(self):
        return getattr(asyncio, 'all_tasks', asyncio.Task.all_tasks)

    async def doCleanups(self):
        outcome = self._outcome or unittest.mock._Outcome()

        while self._cleanups:
            function, args, kwargs = self._cleanups.pop()
            with outcome.testPartExecutor(self):
                if asyncio.iscoroutinefunction(function):
                    await self.loop.create_task(function(*args, **kwargs))
                elif asyncio.iscoroutine(function):
                    await function
                else:
                    function(*args, **kwargs)

        return outcome.success


class BaseTestCase(AsyncTestCase):
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
