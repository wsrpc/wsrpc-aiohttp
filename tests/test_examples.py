import runpy
from pathlib import Path
from uuid import UUID

import pytest
from aiohttp import web

from wsrpc_aiohttp import ClientException, WSRPCClient

EXAMPLES = Path(__file__).resolve().parents[1] / "docs/source/examples"


async def test_quick_start_files(aiohttp_client, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    server = runpy.run_path(str(EXAMPLES / "main/server.py"))
    example_client = runpy.run_path(str(EXAMPLES / "main/client.py"))
    http = await aiohttp_client(server["create_app"]())
    response = await http.get("/web-client.html")
    assert response.status == 200
    assert "uuid4" in await response.text()
    script = await http.get("/js/wsrpc.min.js")
    assert script.status == 200
    assert len(await script.read()) > 1000
    await example_client["main"](str(http.make_url("/ws/")))
    assert UUID(capsys.readouterr().out.strip()).version == 4


async def test_demo_callbacks(aiohttp_client):
    server = runpy.run_path(str(EXAMPLES / "server.py"))
    example_client = runpy.run_path(str(EXAMPLES / "client.py"))
    app = web.Application()
    app.router.add_get("/ws/", server["WebSocket"])
    http = await aiohttp_client(app)
    client = WSRPCClient(str(http.make_url("/ws/")))
    client.add_route("joke", example_client["joke"])
    async with client:
        assert await client.proxy.test(message="Hello") == {"message": "Hello"}
        assert await client.proxy.test.getJoke() == "Cool"
        with pytest.raises(ClientException):
            await client.proxy.test._secure_method()
