from wsrpc_aiohttp import WSRPCClient


async def test_json_text_and_custom_serializer(client: WSRPCClient, handler):
    def echo(socket, **payload):
        return payload

    handler.add_route("echo", echo)
    async with client:
        result = await client.proxy.echo(
            text="Привет 👋", data=b"hello", nested=[True, None, {"x": 42}]
        )
        assert result == {
            "text": "Привет 👋",
            "data": "aGVsbG8=",
            "nested": [True, None, {"x": 42}],
        }
