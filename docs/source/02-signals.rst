Signals
=======

Signals allow to set callbacks on some events:

-  ``ON_CONN_OPEN(socket, request)`` - when new websocket connection
   establishing, before authentication
-  ``ON_CONN_CLOSE(socket, request)`` - right before closing a
   connection
-  ``ON_CONN_FAIL(socket, request, err)`` - on connection upgrade failure
-  ``ON_AUTH_SUCCESS(socket, request)`` - after successfully
   authenticate new connection
-  ``ON_AUTH_FAIL(socket, request)`` - on authentication failure
-  ``ON_CALL_START(method, serial, args, kwargs)`` - on procedure call,
   before executing corresponding handler
-  ``ON_CALL_SUCCESS(method, serial, args, kwargs)`` - on success
   procedure call, before sending a reply
-  ``ON_CALL_FAIL(method, serial, args, kwargs)`` - on exception raised
   from procedure handler

Example:

.. code:: python

   import asyncio
   import logging
   import random
   from contextvars import ContextVar
   from time import time

   import aiohttp.web
   from wsrpc_aiohttp import (
       Route, STATIC_DIR, WebSocketAsync, WebSocketRoute, decorators
   )


   call_started_at = ContextVar("call_started_at")

   log = logging.getLogger(__name__)


   class TestRoute(Route):

       @decorators.proxy
       async def slow_proc(self):
           await asyncio.sleep(random.randint(1, 10) / 10)
           return True

   # Signal handlers
   async def on_call_start(method, **kwargs):
       ts = time()
       log.debug("Method %s called at %f", method, ts)
       call_started_at.set(ts)


   async def on_call_end(method, **kwargs):
       ts = time() - call_started_at.get()
       log.info("Method %s processed for %f", method, ts)

   # Connecting handlers to signals
   WebSocketAsync.ON_CALL_START.connect(on_call_start)
   WebSocketAsync.ON_CALL_SUCCESS.connect(on_call_end)


   app = aiohttp.web.Application()
   app.router.add_route("*", "/ws/", WebSocketAsync)  # Websocket route
   app.router.add_static('/', ".")  # Your static files

   WebSocketAsync.add_route('test', TestRoute)


   if __name__ == '__main__':
       logging.basicConfig(level=logging.INFO)
       aiohttp.web.run_app(app, port=8000, access_log=None)
