"""Exercise default and application-owned serialization across real sockets."""

import json
from dataclasses import dataclass
from functools import partial
from typing import Any

import pytest
from aiohttp.web import Application

from wsrpc_aiohttp import WebSocketAsync, WSRPCClient, serializer
from wsrpc_aiohttp.websocket.tools import json_dumps


@dataclass
class Payload:
    value: int


@serializer.register(Payload)
def encode_payload(value: Payload) -> dict[str, int]:
    return {"registered": value.value}


@pytest.mark.parametrize("dumps", [None, json.dumps, json_dumps])
async def test_registered_types_and_bytes_in_both_directions(
    aiohttp_client, dumps
):
    class RPC(WebSocketAsync):
        pass

    async def reply(socket, value, binary):
        assert value == {"registered": 21}
        assert binary == "aGVsbG8="
        return {"value": Payload(42), "binary": b"world"}

    options = {} if dumps is None else {"dumps": dumps}
    RPC.configure(**options)
    RPC.add_route("reply", reply)
    application = Application()
    application.router.add_route("*", "/ws/", RPC)
    session = await aiohttp_client(application)
    async with WSRPCClient("/ws/", session=session, **options) as client:
        assert await client.call(
            "reply", value=Payload(21), binary=b"hello"
        ) == {
            "value": {"registered": 42},
            "binary": "d29ybGQ=",
        }


@pytest.mark.parametrize("kind", ["function", "partial", "object"])
async def test_custom_codec_controls_its_default(aiohttp_client, kind):
    calls = []

    def own_serializer(value: Payload) -> dict[str, int]:
        # The library's registered serializer intentionally returns another key.
        return {"application": value.value}

    def encode(value: Any) -> str:
        calls.append(value)
        return json.dumps(value, default=own_serializer)

    class Encoder:
        def __call__(self, value: Any) -> str:
            return encode(value)

    dumps = {
        "function": encode,
        "partial": partial(json.dumps, default=own_serializer),
        "object": Encoder(),
    }[kind]

    class RPC(WebSocketAsync):
        pass

    async def reply(socket, value):
        assert value == {"application": 21}
        return Payload(42)

    RPC.configure(dumps=dumps)
    RPC.add_route("reply", reply)
    application = Application()
    application.router.add_route("*", "/ws/", RPC)
    session = await aiohttp_client(application)
    async with WSRPCClient("/ws/", session=session, dumps=dumps) as client:
        assert await client.call("reply", value=Payload(21)) == {
            "application": 42
        }
    if kind != "partial":
        assert len(calls) >= 2  # Both client request and server response.


def test_json_helper_accepts_an_explicit_default():
    assert json.loads(
        json_dumps(Payload(1), default=lambda value: {"own": value.value})
    ) == {"own": 1}
