import logging
import uuid
from pathlib import Path

from aiohttp import web

from wsrpc_aiohttp import STATIC_DIR, WebSocketAsync


class Socket(WebSocketAsync):
    pass


async def get_random_uuid(socket: Socket) -> str:
    return str(uuid.uuid4())


def create_app() -> web.Application:
    Socket.add_route("uuid4", get_random_uuid)
    app = web.Application()
    app.router.add_get("/ws/", Socket)
    app.router.add_static("/js/", STATIC_DIR)
    app.router.add_static("/", Path(__file__).parent)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(create_app(), host="127.0.0.1", port=8000)
