import json
import logging
from asyncio import Lock
from typing import Optional, Union

import aiohttp
from yarl import URL

from .common import WSRPCBase
from .tools import Lazy, awaitable

log = logging.getLogger(__name__)
SocketType = Optional[aiohttp.ClientWebSocketResponse]


class WSRPCClient(WSRPCBase):
    """WSRPC Client class"""

    def __init__(
        self,
        endpoint: Union[URL, str],
        loop=None,
        timeout=None,
        session: Optional[aiohttp.ClientSession] = None,
        loads=json.loads,
        dumps=json.dumps,
        **kwargs,
    ):
        WSRPCBase.__init__(
            self, loop=loop, timeout=timeout, loads=loads, dumps=dumps
        )
        self._url = URL(str(endpoint))
        self._session = session or aiohttp.ClientSession(**kwargs)
        self.send_lock = Lock()

        self.socket: SocketType = None
        self.closed = False

    # noinspection PyMethodOverriding
    async def close(self):
        """Close the client connect connection"""

        if self.closed:
            return

        await super().close()

        if self.socket:
            await self.socket.close()

        await self._session.close()

    async def connect(self):
        """Perform connection to the server"""

        self.socket = await self._session.ws_connect(str(self._url))
        self._create_task(self.__handle_connection())

    async def __handle_connection(self):
        while True:
            async for message in self.socket:  # type: aiohttp.WSMessage
                await self._on_message(message)
            else:
                log.info("Connection was closed")
                self._loop.create_task(self.close())
                break

    async def _send(self, **kwargs):
        try:
            log.debug(
                "Sending message to %s serial %s: %s",
                self._url,
                Lazy(lambda: kwargs.get("id")),
                Lazy(lambda: kwargs),
            )

            if self.socket.closed:
                raise aiohttp.ClientConnectionError("Connection was closed.")

            async with self.send_lock:
                return await self.socket.send_json(kwargs, dumps=self._dumps)
        except aiohttp.WebSocketError:
            self._loop.create_task(self.close())
            raise

    async def _executor(self, func):
        """Method which implements execution of the client functions"""
        return await awaitable(func)()

    async def __aenter__(self):
        if self.socket is None:
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.closed:
            return

        await self.close()


__all__ = ("WSRPCClient",)
