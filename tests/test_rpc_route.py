import asyncio
import uuid

import pytest
from async_timeout import timeout
from wsrpc_aiohttp import (
    AllowedRoute,
    ClientException,
    PrefixRoute,
    Route,
    WebSocketAsync,
    WebSocketRoute,
    WSRPCClient,
    decorators,
)


DATA_TO_RETURN = 1000


class Mixin:
    @decorators.noproxy
    def foo(self):
        return "bar"


class ReverseRouteAllowed(AllowedRoute, Mixin):
    def init(self, data):
        self.data = data

    def reverse(self):
        self.data = self.data[::-1]

    def get_data(self):
        return self.data

    @decorators.noproxy
    def private(self):
        return "Secret"

    def _hack_me(self):
        return "Secret 2"

    async def broadcast(self):
        await self.socket.broadcast("broadcast", result=True)


class ReverseRouteLegacy(WebSocketRoute, Mixin):
    def init(self, data):
        self.data = data

    def reverse(self):
        self.data = self.data[::-1]

    def get_data(self):
        return self.data

    @WebSocketRoute.noproxy
    def private(self):
        return "Secret"

    async def broadcast(self):
        await self.socket.broadcast("broadcast", result=True)


class ReverseRoutePrefix(PrefixRoute, Mixin):
    def rpc_init(self, data):
        self.data = data

    def rpc_reverse(self):
        self.data = self.data[::-1]

    def rpc_get_data(self):
        return self.data

    @decorators.noproxy
    def rpc_private(self):
        return "Secret"

    async def rpc_broadcast(self):
        await self.socket.broadcast("broadcast", result=True)


class ReverseRoute(Route, Mixin):
    @decorators.proxy
    def init(self, data):
        self.data = data

    @decorators.proxy
    def reverse(self):
        self.data = self.data[::-1]

    @decorators.proxy
    def get_data(self):
        return self.data

    @decorators.noproxy
    def private(self):
        return "Secret"

    @decorators.proxy
    async def broadcast(self):
        await self.socket.broadcast("broadcast", result=True)


IMPLEMENTATIONS = (
    ReverseRoute,
    ReverseRouteAllowed,
    ReverseRouteLegacy,
    ReverseRoutePrefix,
)


@pytest.fixture(scope="module", params=IMPLEMENTATIONS)
def route(request):
    return request.param


async def test_call(
    client: WSRPCClient, handler: WebSocketAsync, route: Route
):
    async with client:
        handler.add_route("reverse", route)

        data = str(uuid.uuid4())

        await client.proxy.reverse(data=data)
        await client.proxy.reverse.reverse()

        response = await client.proxy.reverse.get_data()

        assert response == data[::-1]


async def test_broadcast(
    client: WSRPCClient, handler: WebSocketAsync, route: Route, loop
):
    async with client:
        future = loop.create_future()

        async def on_broadcast(_, result):
            nonlocal future
            future.set_result(result)

        client.add_route("broadcast", on_broadcast)
        handler.add_route("reverse", route)

        await client.proxy.reverse(data=None)
        await asyncio.wait_for(client.proxy.reverse.broadcast(), timeout=999)

        assert await asyncio.wait_for(future, timeout=5)


async def test_call_masked(
    client: WSRPCClient, handler: WebSocketAsync, route: Route
):
    async with client:
        handler.add_route("reverse", route)

        await client.proxy.reverse(data="")

        with pytest.raises(ClientException) as e:
            await client.proxy.reverse.private()

        assert e.value.message == "Method masked"


async def test_call_dash_masked(client: WSRPCClient, handler: WebSocketAsync):
    async with client:
        handler.add_route("reverse", ReverseRouteAllowed)

        await client.proxy.reverse(data="")

        with pytest.raises(ClientException) as e:
            await client.proxy._hack_me()

        assert "not implemented" in e.value.message


async def test_call_not_proxied(
    client: WSRPCClient, handler: WebSocketAsync, route: Route
):
    async with client:
        handler.add_route("reverse", route)
        with pytest.raises(ClientException):
            await client.proxy.reverse.foo()


async def test_call_func(client: WSRPCClient, handler: WebSocketAsync):
    def get_data(_):
        return DATA_TO_RETURN

    handler.add_route("get_data", get_data)

    async with client:
        response = await client.proxy.get_data()
        assert response == DATA_TO_RETURN


async def test_call_method(client: WSRPCClient, handler: WebSocketAsync):
    class DataStore:
        def get_data(self, _):
            return DATA_TO_RETURN

    handler.add_route("get_data", DataStore().get_data)

    async with client:
        response = await client.proxy.get_data()
        assert response == DATA_TO_RETURN


async def test_call_timeout(client: WSRPCClient, handler: WebSocketAsync):
    async def will_sleep_for(_, seconds):
        with timeout(0.5):
            await asyncio.sleep(seconds)
            return DATA_TO_RETURN

    handler.add_route("will_sleep_for", will_sleep_for)

    async with client:
        response = await client.proxy.will_sleep_for(seconds=0.1)
        assert response == DATA_TO_RETURN

        with pytest.raises(ClientException):
            await client.proxy.will_sleep_for(seconds=1)
