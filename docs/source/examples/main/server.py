import asyncio
import logging
import uuid

import aiohttp.web
from wsrpc_aiohttp import STATIC_DIR, WebSocketAsync, WebSocketRoute


loop = asyncio.get_event_loop()
app = aiohttp.web.Application()
log = logging.getLogger(__name__)


app.router.add_route("*", "/ws/", WebSocketAsync)
app.router.add_static("/js", STATIC_DIR)
app.router.add_static("/", ".")


async def get_random_uuid(_: WebSocketAsync, foo):
    return str(uuid.uuid4())


WebSocketAsync.add_route("uuid4", get_random_uuid)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    aiohttp.web.run_app(app, port=8000)
