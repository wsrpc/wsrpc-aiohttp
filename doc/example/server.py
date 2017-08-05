import logging
import aiohttp.web
import asyncio

from wsrpc_aiohttp import WebSocket, STATIC_DIR


loop = asyncio.get_event_loop()
app = aiohttp.web.Application(loop=loop)


app.router.add_route("*", "/ws/", WebSocket)
app.router.add_static('/js', STATIC_DIR)
app.router.add_static('/', ".")


async def simple_route(socket: WebSocket, **kwargs):
    await socket.call('test')
    print('boom')


WebSocket.add_route('test', simple_route)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    aiohttp.web.run_app(app, port=8000)
