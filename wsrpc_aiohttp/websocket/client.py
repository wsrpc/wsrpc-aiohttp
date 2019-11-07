from typing import Union

import aiohttp
import logging

from yarl import URL

from .tools import Lazy, dumps
from .common import WSRPCBase, awaitable

log = logging.getLogger(__name__)


class WSRPCClient(WSRPCBase):
    """ WSRPC Client class """

    def __init__(self, endpoint: Union[URL, str], loop=None, timeout=None,
                 session: aiohttp.ClientSession = None, **kwargs):

        WSRPCBase.__init__(self, loop=loop, timeout=timeout)
        self._url = URL(str(endpoint))
        self._session = session or aiohttp.ClientSession(
            loop=self._loop, **kwargs
        )

        self.socket = None      # type: aiohttp.ClientWebSocketResponse
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

    async def _send(self, **kwargs):
        try:
            log.debug(
                "Sending message to %s serial %s: %s",
                self._url, Lazy(lambda: kwargs.get('id')),
                Lazy(lambda: kwargs),
            )

            if self.socket.closed:
                raise aiohttp.ClientConnectionError('Connection was closed.')

            return await self.socket.send_json(kwargs, dumps=lambda x: dumps(x))
        except aiohttp.WebSocketError:
            self._loop.create_task(self.close())
            raise

    async def _executor(self, func):
        """ Method which implements execution of the client functions """
        return await awaitable(func)()

    async def __aenter__(self):
        if self.socket is None:
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.closed:
            return

        await self.close()


__all__ = 'WSRPCClient',
