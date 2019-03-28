import abc
import types
from collections import defaultdict
from functools import partial

import asyncio
import logging
from typing import Union, Callable, Any, Dict

import aiohttp

from .tools import loads
from .route import WebSocketRoute


class ClientException(Exception):
    pass


class PingTimeoutError(Exception):
    pass


def ping(obj, **kwargs):
    return kwargs


log = logging.getLogger(__name__)
RouteType = Union[Callable[['WSRPCBase', Any], Any], WebSocketRoute]


class _ProxyMethod:
    __slots__ = '__call', '__name'

    def __init__(self, call_method, name):
        self.__call = call_method
        self.__name = name

    def __call__(self, **kwargs):
        return self.__call(self.__name, **kwargs)

    def __getattr__(self, item: str):
        return self.__class__(self.__call, ".".join((self.__name, item)))


class _Proxy:
    __slots__ = '__call',

    def __init__(self, call_method):
        self.__call = call_method

    def __getattr__(self, item: str):
        return _ProxyMethod(self.__call, item)


class WSRPCBase:
    """ Common WSRPC abstraction """

    _ROUTES = defaultdict(lambda: {'ping': ping})
    _CLIENTS = defaultdict(dict)
    _CLEAN_LOCK_TIMEOUT = 2

    __slots__ = ('_handlers', '_loop', '_pending_tasks', '_locks',
                 '_futures', '_serial', '_timeout')

    def __init__(self, loop: asyncio.AbstractEventLoop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._handlers = {}
        self._pending_tasks = set()
        self._serial = 0
        self._timeout = None
        self._locks = defaultdict(partial(asyncio.Lock, loop=self._loop))
        self._futures = defaultdict(self._loop.create_future)

    def _create_task(self, coro):
        task = self._loop.create_task(coro)      # type: asyncio.Task
        self._pending_tasks.add(task)
        task.add_done_callback(partial(self._pending_tasks.remove))

        return task

    def _call_later(self, timer, callback, *args, **kwargs):
        def handler():
            self._create_task(asyncio.coroutine(callback)(*args, **kwargs))

        self._pending_tasks.add(self._loop.call_later(timer, handler))

    async def close(self):
        """ Cancel all pending tasks """
        async def task_waiter(task):
            if not (hasattr(task, '__iter__') or hasattr(task, '__aiter__')):
                return

            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception(
                    "Unhandled exception when closing client connection"
                )

        for task in tuple(self._pending_tasks):
            task.cancel()

            if hasattr(task, 'cancelled') and not task.cancelled():
                self._loop.create_task(task_waiter(task))

    def _log_call(self, start: float, *args):
        end = self._loop.time()
        log.info(end - start)

    async def _handle_message(self, msg: aiohttp.WSMessage):
        if msg.type == aiohttp.WSMsgType.TEXT:
            self._create_task(self.on_message(msg))
        elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED):
            self._create_task(self.close())
        elif msg.type == aiohttp.WSMsgType.ERROR:
            self._create_task(self.close())
            raise aiohttp.WebSocketError(code=msg.type.value, message=msg)
        else:
            log.warning("Unhandled message %r %r", msg.type, msg.data)

    @classmethod
    def get_routes(cls) -> Dict[str, RouteType]:
        return cls._ROUTES[cls]

    @classmethod
    def get_clients(cls) -> Dict[str, 'WSRPCBase']:
        return cls._CLIENTS[cls]

    @property
    def routes(self) -> Dict[str, RouteType]:
        """ Property which contains the socket routes """
        return self.get_routes()

    @property
    def clients(self) -> Dict[str, 'WSRPCBase']:
        """ Property which contains the socket clients """
        return self.get_clients()

    @staticmethod
    def _prepare_args(args):
        arguments = []
        kwargs = {}

        if isinstance(args, type(None)):
            return arguments, kwargs

        if isinstance(args, list):
            arguments.extend(args)
        elif isinstance(args, dict):
            kwargs.update(args)
        else:
            arguments.append(args)

        return arguments, kwargs

    async def on_message(self, message: aiohttp.WSMessage):
        # deserialize message
        data = message.json(loads=loads)

        log.debug("Response: %r", data)
        serial = data.get('id')
        method = data.get('method')
        result = data.get('result')
        error = data.get('error')

        log.debug("Acquiring lock for %s serial %s", self, serial)
        async with self._locks[serial]:
            try:
                if 'method' in data:
                    args, kwargs = self._prepare_args(
                        data.get('params', None)
                    )

                    callee = self.resolver(method)
                    calee_is_route = (
                        hasattr(callee, '__self__') and
                        isinstance(callee.__self__, WebSocketRoute)
                    )

                    if not calee_is_route:
                        a = [self]
                        a.extend(args)
                        args = a

                    result = await self._executor(
                        partial(callee, *args, **kwargs)
                    )

                    self._send(result=result, id=serial)
                elif 'result' in data:
                    cb = self._futures.pop(serial, None)
                    cb.set_result(result)

                elif 'error' in data:
                    self._reject(serial, error)
                    log.error('Client return error: \n\t%r', error)

            except Exception as e:
                log.exception(e)
                if not serial:
                    return

                self._send(error=self._format_error(e), id=serial)

            finally:
                def clean_lock():
                    log.debug(
                        "Release and delete lock for %s serial %s",
                        self, serial
                    )

                    if serial in self._locks:
                        self._locks.pop(serial)

                self._call_later(self._CLEAN_LOCK_TIMEOUT, clean_lock)

    @abc.abstractstaticmethod
    def _send(self, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _format_error(e):
        return {'type': str(type(e).__name__), 'message': str(e)}

    def _reject(self, serial, error):
        future = self._futures.get(serial)

        if not future:
            return

        future.set_exception(ClientException(error))

    def _unresolvable(self, func_name, *args, **kwargs):
        raise NotImplementedError(
            'Callback function "%r" not implemented' % func_name
        )

    def resolver(self, func_name):
        class_name, method = (
            func_name.split('.') if '.' in func_name else (func_name, 'init')
        )

        callee = self.routes.get(class_name, self._unresolvable)

        condition = (
            callee == self._unresolvable or
            isinstance(getattr(callee, '__self__', None), WebSocketRoute) or (
                not isinstance(callee, (types.FunctionType, types.MethodType))
                and issubclass(callee, WebSocketRoute)
            )
        )

        if condition:
            if class_name not in self._handlers:
                self._handlers[class_name] = callee(self)

            return self._handlers[class_name]._resolve(method)  # noqa

        callee = self.routes.get(func_name, self._unresolvable)
        if hasattr(callee, '__call__'):
            return callee
        else:
            raise NotImplementedError(
                'Method call of {0} is not implemented'.format(repr(callee))
            )

    def _get_serial(self):
        self._serial += 2
        return self._serial

    def call(self, func: str, **kwargs):
        """ Method for call remote function

        Remote methods allows only kwargs as arguments.

        You might use functions as route or classes

        .. code-block:: python

            async def remote_function(socket: WSRPCBase, *, foo, bar):
                # call function from the client-side
                await self.socket.proxy.ping()
                return foo + bar

            class RemoteClass(WebSocketRoute):

                # this method executes when remote side call route name
                asyc def init(self):
                    # call function from the client-side
                    await self.socket.proxy.ping()

                async def make_something(self, foo, bar):
                    return foo + bar

        """
        serial = self._get_serial()

        future = self._futures[serial]

        payload = dict(id=serial, method=func, params=kwargs)

        log.debug("Sending: %r", payload)
        send_future = self._send(**payload)

        log.info("Sending request #%r \"%s(%r)\" to the client.",
                 serial, func, kwargs)

        future = asyncio.ensure_future(asyncio.wait_for(
            future, self._timeout,
            loop=self._loop), loop=self._loop
        )

        def propagate_exception(f):
            if f.exception():
                future.set_exception(f.exception())
        if send_future:
            send_future.add_done_callback(propagate_exception)
        return future

    @classmethod
    def add_route(cls, route: str, handler: Union[WebSocketRoute, Callable]):
        """ Expose local function through RPC

        :param route: Name which function will be aliased for this function.
                      Remote side should call function by this name.
        :param handler: Function or Route class (classes based on
                        :class:`wsrpc_aiohttp.WebSocketRoute`).
                        For route classes the public methods will
                        be registered automatically.

        .. note::

            Route classes might be initialized only once for the each
            socket instance.

            In case the method of class will be called first,
            :func:`wsrpc_aiohttp.WebSocketRoute.init` will be called
            without params before callable method.

        """
        assert callable(handler) or isinstance(handler, WebSocketRoute)
        cls.get_routes()[route] = handler

    @classmethod
    def remove_route(cls, route: str, fail=True):
        """ Removes route by name. If `fail=True` an exception
        will be raised in case the route was not found. """

        if fail:
            cls.get_routes().pop(route)
        else:
            cls.get_routes().pop(route, None)

    def __repr__(self):
        if hasattr(self, 'id'):
            return "<RPCWebSocket: ID[{0}]>".format(self.id)
        else:
            return "<RPCWebsocket: {0} (waiting)>".format(self.__hash__())

    @abc.abstractstaticmethod
    async def _executor(self, func):
        raise NotImplementedError

    @property
    def proxy(self):
        """ Special property which allow run the remote functions
        by `dot` notation

        .. code-block:: python

            # calls remote function with name ping
            await client.proxy.ping()

            # full equivalent of
            await client.call('ping')
        """
        return _Proxy(self.call)
