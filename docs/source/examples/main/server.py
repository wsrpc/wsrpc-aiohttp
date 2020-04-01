import asyncio
import logging
import uuid

import aiohttp.web
from wsrpc_aiohttp import STATIC_DIR, WebSocketAsync


loop = asyncio.get_event_loop()
app = aiohttp.web.Application(loop=loop)
log = logging.getLogger(__name__)


app.router.add_route("*", "/ws/", WebSocketAsync)
app.router.add_static("/js", STATIC_DIR)
app.router.add_static("/", ".")


def get_random_uuid(socket: WebSocketAsync):
    return str(uuid.uuid4())


WebSocketAsync.add_route("uuid4", get_random_uuid)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    aiohttp.web.run_app(app, port=8000)
