from typing import Any, NamedTuple

from wsrpc_aiohttp import WSRPCClient, serializer
from wsrpc_aiohttp.websocket.tools import json_dumps


async def test_call_error(client: WSRPCClient, handler):

    handler.configure(dumps=json_dumps)

    class CustomType(NamedTuple):
        name: str
        value: Any

    @serializer.register(CustomType)
    def _serizlize(value: CustomType):
        return {
            "custom_type": {
                "name": value.name,
                "value": serializer(value.value),
            },
        }

    async def handle_request(_):
        return CustomType(name="the answer", value=42)

    handler.add_route("send_custom", handle_request)

    async with client:
        result = await client.call("send_custom")

    assert result
