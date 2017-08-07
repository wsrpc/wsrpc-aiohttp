from typing import Union

import aiohttp
import logging

import asyncio
from yarl import URL

from .tools import Lazy, json
from .common import WSRPCBase


log = logging.getLogger(__name__)


class WSRPCClient(WSRPCBase):

    def __init__(self, endpoint: Union[URL, str], loop=None):
        WSRPCBase.__init__(self, loop=loop)
        self._url = URL(str(endpoint))
        self._session = aiohttp.ClientSession(loop=self._loop)
        self.socket = None
        self.closed = False

    async def close(self):
        if self.closed:
            return

        await super().close()

        if self.socket:
            await self.socket.close()

        await self._session.close()

    async def connect(self):
        self.socket = await self._session.ws_connect(str(self._url))
        self._create_task(self.__handle_connection())

    async def __handle_connection(self):
        while True:
            async for message in self.socket:    # type: aiohttp.WSMessage
                await self._handle_message(message)
            else:
                log.info('Connection was closed')

    def _send(self, **kwargs):
        try:
            log.debug(
                "Sending message to %s serial %s: %s",
                self._url,
                Lazy(lambda: str(kwargs.get('serial'))),
                Lazy(lambda: str(kwargs))
              )
            self._loop.create_task(self.socket.send_json(kwargs, dumps=json.dumps))
        except aiohttp.WebSocketError:
            self._loop.create_task(self.close())

    async def _executor(self, func):
        await asyncio.coroutine(func)()
