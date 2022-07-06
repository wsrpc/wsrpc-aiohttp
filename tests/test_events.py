from wsrpc_aiohttp import WSRPCBase, WSRPCClient


async def emitter(socket: WSRPCBase):
    await socket.emit({"Hello": "world"})


async def test_emitter(client: WSRPCClient, handler, event_loop):
    handler.add_route("emitter", emitter)

    async with client:
        future = event_loop.create_future()

        client.add_event_listener(future.set_result)

        await client.proxy.emitter()
        result = await future

        assert result == {"Hello": "world"}
