# encoding: utf-8
import asyncio
import logging
import uuid
from collections import defaultdict

import aiohttp
from aiohttp import web, WebSocketError
from aiohttp.abc import AbstractView

from .common import WSRPCBase, ClientException, awaitable
from .route import WebSocketRoute
from .tools import Lazy, dumps

global_log = logging.getLogger("wsrpc")
log = logging.getLogger("wsrpc.handler")


class WebSocketBase(WSRPCBase, AbstractView):
    """ Base class for aiohttp websocket handler """

    __slots__ = ('_request', 'socket', 'id', '__pending_tasks',
                 '__handlers', 'store', 'serial', '_ping', 'protocol_version')

    KEEPALIVE_PING_TIMEOUT = 30        # type: int
    CLIENT_TIMEOUT = int(KEEPALIVE_PING_TIMEOUT / 3)    # type: int
    MAX_CONCURRENT_REQUESTS = 25       # type: int
    REQUEST_EXECUTION_TIMEOUT = None   # type: int

    def __init__(self, request):
        AbstractView.__init__(self, request)
        WSRPCBase.__init__(self, timeout=self.REQUEST_EXECUTION_TIMEOUT)

        self._ping = defaultdict(self._loop.create_future)
        self.id = uuid.uuid4()
        self.protocol_version = None
        self.serial = 0
        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

    @classmethod
    def configure(cls, keepalive_timeout=KEEPALIVE_PING_TIMEOUT,
                  client_timeout=CLIENT_TIMEOUT,
                  max_concurrent_requests=MAX_CONCURRENT_REQUESTS):
        """ Configures the handler class

        :param keepalive_timeout: sets timeout of client pong response
        :param client_timeout: internal lock timeout
        :param max_concurrent_requests: how many concurrent requests might
                                        be performed by each client
        """

        cls.KEEPALIVE_PING_TIMEOUT = keepalive_timeout
        cls.CLIENT_TIMEOUT = client_timeout
        cls.MAX_CONCURRENT_REQUESTS = max_concurrent_requests

    def __await__(self):
        return self.__handle_request().__await__()

    async def authorize(self) -> bool:
        """ Special method for authorize client.
        If this method return True then access allowed,
        otherwise ``403 Forbidden`` will be sent.

        This method will be called before socket connection establishment.

        By default everyone has access. You have to inherit this class
        and change this behaviour.

        .. note::
            You can validate some headers (self.request.headers) or
            check cookies (self.reauest.cookies).
        """
        return True

    async def __handle_request(self):
        self.socket = web.WebSocketResponse()

        if not await self.authorize():
            raise web.HTTPForbidden()

        await self.socket.prepare(self.request)

        try:
            self.clients[self.id] = self
            self._create_task(self._start_ping())

            async for msg in self.socket:
                try:
                    await self._handle_message(msg)
                except WebSocketError:
                    log.error('Client connection %s closed with exception %s',
                              self.id, self.socket.exception())
                    break
            else:
                log.info('Client connection %s closed', self.id)

            return self.socket
        finally:
            await self.close()

    @classmethod
    def broadcast(cls, func, callback=WebSocketRoute.placebo, **kwargs):
        """ Call remote function on all connected clients

        :param func: Remote route name
        :param callback: Function which receive responses
        """

        loop = asyncio.get_event_loop()

        tasks = []

        for client in cls.get_clients().values():
            tasks.append(loop.create_task(
                client.call, func, callback, **kwargs
            ))

        return asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    async def _send(self, **kwargs):
        try:
            log.debug(
                "Sending message to %s serial %s: %s",
                Lazy(lambda: str(self.id)),
                Lazy(lambda: str(kwargs.get('id'))),
                Lazy(lambda: str(kwargs))
              )
            await self.socket.send_json(kwargs, dumps=lambda x: dumps(x))
        except aiohttp.WebSocketError:
            self._create_task(self.close())

    @staticmethod
    def _format_error(e):
        return {'type': str(type(e).__name__), 'message': str(e)}

    def _reject(self, serial, error):
        future = self._futures.get(serial)
        if future:
            future.set_exception(ClientException(error))

    async def close(self):
        """ Cancel all pending tasks and stop this socket connection """
        await self.socket.close()
        await super().close()

        if self.id in self.clients:
            self.clients.pop(self.id)

        for name, obj in self._handlers.items():
            self._loop.create_task(awaitable(obj._onclose)())

    def _log_client_list(self):
        log.debug('CLIENTS: %s', Lazy(lambda: ''.join([
            '\n\t%r' % i for i in self.clients.values()
        ])))

    async def _start_ping(self):
        while True:
            if self.socket.closed:
                return

            future = asyncio.ensure_future(
                self.call('ping', seq=self._loop.time())
            )

            def on_timeout():
                if future.done():
                    return

                if isinstance(future, asyncio.Task):
                    future.cancel()
                    return

                future.set_exception(TimeoutError)

            handle = self._loop.call_later(
                self.KEEPALIVE_PING_TIMEOUT, on_timeout
            )

            future.add_done_callback(lambda f: handle.cancel())

            try:
                resp = await future
                if not resp:
                    continue

                delta = (self._loop.time() - resp.get('seq', 0))

                log.debug("%r Pong recieved: %.4f" % (self, delta))

            except asyncio.CancelledError:
                break
            except (TimeoutError, asyncio.TimeoutError):
                log.info('Client "%r" connection should be '
                         'closed because ping timeout', self)

                self._loop.create_task(self.close())
                break
            except Exception:
                log.exception('Error when ping remote side.')
                break

            if delta > self.CLIENT_TIMEOUT:
                log.info('Client "%r" connection should be closed because ping '
                         'response time gather then client timeout', self)
                self._loop.create_task(self.close())
                break

            await asyncio.sleep(self.KEEPALIVE_PING_TIMEOUT)


class WebSocketAsync(WebSocketBase):
    """ Handler class which execute any route as a coroutine """
    async def _executor(self, func):
        return await awaitable(func)()


class WebSocketThreaded(WebSocketBase):
    """ Handler class which execute any route in the default thread-pool
    of current event loop """

    async def _executor(self, func):
        return await self._loop.run_in_executor(None, func)


__all__ = ('WebSocketAsync', 'WebSocketThreaded', 'WebSocketBase')
