from typing import Union

import aiohttp
import logging

import asyncio
from yarl import URL

from .tools import Lazy, dumps
from .common import WSRPCBase


log = logging.getLogger(__name__)


class WSRPCClient(WSRPCBase):
    """ WSRPC Client class """

    def __init__(self, endpoint: Union[URL, str], loop=None, timeout=None,
                 session: aiohttp.ClientSession=None, **kwargs):

        WSRPCBase.__init__(self, loop=loop)
        self._url = URL(str(endpoint))
        self._session = session or aiohttp.ClientSession(
            loop=self._loop, **kwargs
        )

        self._timeout = timeout
        self.socket = None
        self.closed = False

    async def close(self):
        """ Close the client connect connection """

        if self.closed:
            return

        await super().close()

        if self.socket:
            await self.socket.close()

        await self._session.close()

    async def connect(self):
        """ Perform connection to the server """

        self.socket = await self._session.ws_connect(str(self._url))
        self._create_task(self.__handle_connection())

    async def __handle_connection(self):
        while True:
            async for message in self.socket:    # type: aiohttp.WSMessage
                await self._handle_message(message)
            else:
                log.info('Connection was closed')
                self._loop.create_task(self.close())
                break

    def _send(self, **kwargs):
        try:
            log.debug(
                "Sending message to %s serial %s: %s",
                self._url,
                Lazy(lambda: kwargs.get('id')),
                Lazy(lambda: kwargs),
              )

            if self.socket.closed:
                raise aiohttp.ClientConnectionError('Connection was closed.')

            send_coro = self.socket.send_json(kwargs, dumps=lambda x: dumps(x))
            return self._loop.create_task(send_coro)
        except aiohttp.WebSocketError as ex:
            self._loop.create_task(self.close())
            future = self._loop.create_future()
            future.set_exception(ex)
            return future

    async def _executor(self, func):
        """ Method which implements execution of the client functions """
        return await asyncio.coroutine(func)()


__all__ = 'WSRPCClient',
