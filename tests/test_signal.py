import pytest

from aiohttp import WSServerHandshakeError

from wsrpc_aiohttp import ClientException, WebSocketAsync
from wsrpc_aiohttp.signal import Signal


def reset_signals(handler):
    for signal in (
        "ON_AUTH_SUCCESS",
        "ON_AUTH_FAIL",
        "ON_CONN_OPEN",
        "ON_CONN_CLOSE",
        "ON_CALL_START",
        "ON_CALL_SUCCESS",
        "ON_CALL_FAIL",
    ):
        setattr(handler, signal, Signal())


@pytest.fixture
def reset_websocket_signals():
    reset_signals(WebSocketAsync)


async def test_connection_signals(handler, client):
    connected, disconnected = False, False

    async def on_connect(socket, request):
        nonlocal connected
        connected = True

    async def on_disconnect(socket, request):
        nonlocal disconnected
        disconnected = True

    handler.ON_CONN_OPEN.connect(on_connect)
    handler.ON_CONN_CLOSE.connect(on_disconnect)

    assert not connected
    assert not disconnected

    await client.connect()
    assert connected
    assert not disconnected

    await client.close()
    assert connected
    assert disconnected


class TestSuiteAuthSignals:

    class AuthHandler(WebSocketAsync):
        allow_authorize = False

        async def authorize(self):
            return self.allow_authorize

    @pytest.fixture
    def handler(self):
        return self.AuthHandler

    async def test_auth_fail_signal(self, client, handler):
        auth_failed = False

        async def on_auth_fail(socket, request):
            nonlocal auth_failed
            auth_failed = True

        handler.allow_authorize = False
        handler.ON_AUTH_FAIL.connect(on_auth_fail)

        with pytest.raises(WSServerHandshakeError):
            await client.connect()

        assert auth_failed

    async def test_auth_success_signal(self, client, handler):
        auth_success = False

        async def on_auth_success(socket, request):
            nonlocal auth_success
            auth_success = True

        handler.allow_authorize = True
        handler.ON_AUTH_SUCCESS.connect(on_auth_success)

        async with client:
            assert auth_success


class TestSuiteCallProcedureSignals:

    class RPCHandler(WebSocketAsync):
        pass

    @pytest.fixture
    def handler(self):

        async def proc_success(*args, **kwargs):
            return True

        async def proc_fail(*args, **kwargs):
            raise RuntimeError("Error occured")

        self.RPCHandler.add_route("proc_success", proc_success)
        self.RPCHandler.add_route("proc_fail", proc_fail)

        return self.RPCHandler

    async def test_on_call_success_signal(self, client, handler):
        call_started = False
        call_started_args = None
        call_success = False
        call_success_args = None

        async def on_call_start(**kwargs):
            nonlocal call_started
            nonlocal call_started_args
            call_started = True
            call_started_args = kwargs

        async def on_call_success(**kwargs):
            nonlocal call_success
            nonlocal call_success_args
            call_success = True
            call_success_args = kwargs

        handler.ON_CALL_START.connect(on_call_start)
        handler.ON_CALL_SUCCESS.connect(on_call_success)

        async with client:
            assert await client.call("proc_success")

        assert call_started
        assert call_success
        assert call_started_args["method"] == "proc_success"
        assert call_success_args["method"] == "proc_success"

    async def test_on_call_fail_signal(self, client, handler):
        call_started = False
        call_fail = False
        call_fail_args = None

        async def on_call_start(**kwargs):
            nonlocal call_started
            call_started = True

        async def on_call_fail(**kwargs):
            nonlocal call_fail
            nonlocal call_fail_args
            call_fail = True
            call_fail_args = kwargs

        handler.ON_CALL_START.connect(on_call_start)
        handler.ON_CALL_FAIL.connect(on_call_fail)

        async with client:
            with pytest.raises(ClientException):
                assert await client.call("proc_fail")

        assert call_started
        assert call_fail
        assert call_fail_args["method"] == "proc_fail"
