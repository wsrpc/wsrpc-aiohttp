import asyncio
import logging
import time
from binascii import hexlify
from pathlib import Path
from random import choice

import aiohttp.web

from wsrpc_aiohttp import STATIC_DIR, WebSocketAsync, WebSocketRoute

log = logging.getLogger(__name__)


class WebSocket(WebSocketAsync):
    async def handle_binary(self, message: aiohttp.WSMessage):
        await self.proxy.print(
            type=message.type,
            hex=hexlify(message.data).decode(),
            message="Got binary data",
        )


class TestRoute(WebSocketRoute[WebSocket]):
    JOKES = [
        "There are two hard problems: cache invalidation, naming, "
        "and off-by-one errors.",
        "There are 10 kinds of people: those who understand binary "
        "and those who do not.",
        "The generation of random numbers is too important "
        "to be left to chance.",
    ]

    def init(self, **kwargs):
        return kwargs

    async def delayed(self, delay=0):
        await asyncio.sleep(delay)
        return f"I'm delayed {delay} seconds"

    async def getEpoch(self):
        return time.time()

    async def requiredArgument(self, _my_secret_arg):
        return True

    async def _secure_method(self):
        return "This private method is not exposed"

    async def exc(self):
        raise Exception("Test Тест テスト 测试")

    async def getJoke(self):
        joke = choice(self.JOKES)

        result = await self.socket.proxy.joke(joke=joke)
        log.info(
            'Client said that was "%s"', ("awesome" if result else "awful")
        )
        return "Cool" if result else "Hmm.. Try again."


WebSocket.add_route("test", TestRoute)


if __name__ == "__main__":
    from argparse import ArgumentParser

    logging.basicConfig(level=logging.DEBUG)

    parser = ArgumentParser()
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)

    arguments = parser.parse_args()
    app = aiohttp.web.Application()
    app.router.add_route("*", "/ws/", WebSocket)
    app.router.add_static("/js", STATIC_DIR)

    async def redirect(_) -> aiohttp.web.Response:
        return aiohttp.web.HTTPFound("/index.html")

    app.router.add_route("GET", "/", redirect)
    app.router.add_static("/", Path(__file__).parent)
    aiohttp.web.run_app(app, port=arguments.port, host=arguments.listen)
