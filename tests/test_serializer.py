from typing import Any, NamedTuple

import pytest
from aiohttp.web import Application

from wsrpc_aiohttp import WSRPCClient, serializer
from wsrpc_aiohttp.websocket.tools import json_dumps


@pytest.fixture
def application(handler, socket_path):
    app = Application()
    handler.configure(dumps=json_dumps)
    app.router.add_route("*", socket_path, handler)
    return app


async def test_call_error(client: WSRPCClient, handler):
    class CustomType:
        name: str
        value: Any

        def __init__(self, name, value):
            self.name = name
            self.value = value

    @serializer.register(CustomType)
    def _serialize(value: CustomType):
        return {
            "custom_type": {
                "name": value.name,
                "value": value.value,
            },
        }

    assert serializer(CustomType("foo", "bar")) == {
        "custom_type": {"name": "foo", "value": "bar"},
    }

    async def handle_request(_):
        return CustomType(name="the answer", value=42)

    handler.add_route("send_custom", handle_request)

    async with client:
        result = await client.call("send_custom")

    assert result == {"custom_type": {"name": "the answer", "value": 42}}
