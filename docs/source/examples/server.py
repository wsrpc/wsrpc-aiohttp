import logging
import time

import aiohttp.web
import asyncio
from random import choice

from wsrpc_aiohttp import WebSocketAsync, STATIC_DIR, WebSocketRoute

loop = asyncio.get_event_loop()
app = aiohttp.web.Application(loop=loop)
log = logging.getLogger(__name__)


app.router.add_route("*", "/ws/", WebSocketAsync)
app.router.add_static('/js', STATIC_DIR)
app.router.add_static('/', ".")


class TestRoute(WebSocketRoute):
    JOKES = [
        '[ $[ $RANDOM % 6 ] == 0 ] && rm -rf / || echo *Click*',
        'It’s always a long day, 86,400 won’t fit into a short.',
        'Programming is like sex:\nOne mistake and you have to support it for the rest of your life.',
        'There are three kinds of lies: lies, damned lies, and benchmarks.',
        'The generation of random numbers is too important to be left to chance.',
        'A SQL query goes to a restaurant, walks up to 2 tables and says “Can I join you”?',
    ]

    def init(self, **kwargs):
        return kwargs

    async def delayed(self, delay=0):
        await asyncio.sleep(delay)
        return "I'm delayed {0} seconds".format(delay)

    async def getEpoch(self):
        return time.time()

    async def requiredArgument(self, _my_secret_arg):
        return True

    async def _secure_method(self):
        return 'WTF???'

    async def exc(self):
        raise Exception(u"Test Тест テスト 测试")

    async def getJoke(self):
        joke = choice(self.JOKES)

        result = await self.socket.proxy.joke(joke=joke)
        log.info(
            'Client said that was "%s"',
            ('awesome' if result else 'awful')
        )
        return 'Cool' if result else 'Hmm.. Try again.'


WebSocketAsync.add_route('test', TestRoute)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    aiohttp.web.run_app(app, port=8000)
