import abc
import asyncio
import json
import logging
import types
import typing as t
from collections import defaultdict
from functools import partial

import aiohttp

from wsrpc_aiohttp.signal import Signal

from . import decorators
from .abc import (
    AbstractWSRPC,
    ClientCollectionType,
    DumpsType,
    EventListenerCollectionType,
    EventListenerType,
    FrameMappingItemType,
    FutureCollectionType,
    LoadsType,
    LocksCollectionType,
    Proxy,
    RouteCollectionType,
    RouteType,
    TimeoutType,
)
from .route import Route
from .tools import Singleton, awaitable, serializer


class WSRPCError(Exception):
    pass


class ClientException(WSRPCError):
    __slots__ = ("type", "message", "raw")

    def __init__(self, payload):
        self.type = payload.get("type")
        self.message = payload.get("message")
        self.raw = payload


class PingTimeoutError(WSRPCError):
    pass


def ping(_, **kwargs):
    return kwargs


log = logging.getLogger(__name__)


class Nothing(Singleton):
    def __repr__(self):
        return self.__class__.__name__


CallItem = t.NamedTuple(
    "CallItem",
    (
        ("serial", t.Optional[int]),
        ("method", t.Union[Nothing, str, None]),
        ("error", t.Union[Nothing, t.Any]),
        ("result", t.Union[Nothing, t.Any]),
        ("params", t.Optional[t.Union[t.List, t.Dict]]),
    ),
)


def _route_maker() -> t.Dict[str, RouteType]:
    return {"ping": ping}  # type: ignore


class WSRPCBase(AbstractWSRPC):
    """Common WSRPC abstraction"""

    _ROUTES: RouteCollectionType = defaultdict(_route_maker)
    _CLIENTS: ClientCollectionType = defaultdict(dict)
    _CLEAN_LOCK_TIMEOUT: t.Union[int, float] = 2

    __slots__ = (
        "_handlers",
        "_loop",
        "_pending_tasks",
        "_locks",
        "_futures",
        "_serial",
        "_timeout",
        "_event_listeners",
        "_message_type_mapping",
    )

    ON_CALL_START = Signal()
    ON_CALL_SUCCESS = Signal()
    ON_CALL_FAIL = Signal()

    _pending_tasks: t.Set[t.Union[asyncio.Task, asyncio.Handle]]
    _handlers: t.Dict[str, RouteType]

    def _dumps(self, value: t.Any) -> t.Any:
        return self._json_dumps(value, default=serializer)

    def __init__(
        self,
        loop: t.Optional[asyncio.AbstractEventLoop] = None,
        timeout: t.Optional[TimeoutType] = None,
        loads: LoadsType = json.loads,
        dumps: DumpsType = json.dumps,
    ):
        self._json_dumps = dumps
        self._json_loads = loads
        self._loop = loop or asyncio.get_event_loop()
        self._handlers = {}
        self._pending_tasks = set()
        self._serial = 0
        self._timeout: t.Optional[TimeoutType] = timeout
        self._locks: LocksCollectionType = defaultdict(asyncio.Lock)
        self._futures: FutureCollectionType = defaultdict(
            self._loop.create_future
        )
        self._event_listeners: EventListenerCollectionType = set()
        self._message_type_mapping = self._create_type_mapping()

    def _create_type_mapping(self) -> FrameMappingItemType:
        return types.MappingProxyType(
            {
                aiohttp.WSMsgType.TEXT: self.handle_message,
                aiohttp.WSMsgType.BINARY: self.handle_binary,
                aiohttp.WSMsgType.CLOSE: self.close,
                aiohttp.WSMsgType.CLOSED: self.close,
            }
        )

    def _create_task(self, coro):
        task: asyncio.Task = self._loop.create_task(coro)
        self._pending_tasks.add(task)
        task.add_done_callback(partial(self._pending_tasks.remove))

        return task

    def _call_later(self, timer, callback, *args, **kwargs):
        def handler():
            self._create_task(awaitable(callback)(*args, **kwargs))

        self._pending_tasks.add(self._loop.call_later(timer, handler))

    async def close(self, message=None):
        """Cancel all pending tasks"""

        async def task_waiter(task):
            if not (hasattr(task, "__iter__") or hasattr(task, "__aiter__")):
                return

            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception(
                    "Unhandled exception when closing client connection"
                )

        if message:
            log.info("Closing WebSocket because message %r received", message)

        for task in tuple(self._pending_tasks):
            task.cancel()

            if hasattr(task, "cancelled") and not task.cancelled():
                self._loop.create_task(task_waiter(task))

    async def handle_binary(self, message: aiohttp.WSMessage):
        log.warning("Unhandled message %r %r", message.type, message.data)

    async def _call_method(self, call_item: CallItem):
        try:
            if not isinstance(call_item.method, Nothing) and call_item.serial:
                log.debug(
                    "Acquiring lock for %r serial %r", self, call_item.serial
                )
                async with self._locks[call_item.serial]:
                    args, kwargs = self.prepare_args(call_item.params)

                    return await self.handle_method(
                        call_item.method, call_item.serial, args, kwargs
                    )
            elif not isinstance(call_item.result, Nothing):
                return await self.handle_result(
                    call_item.serial, call_item.result
                )
            elif not isinstance(call_item.error, Nothing):
                return await self.handle_error(
                    call_item.serial, call_item.error
                )
            else:
                return await self.handle_result(call_item.serial, None)

        except Exception as e:
            log.exception(e)

            if call_item.serial:
                await self._send(
                    error=self._format_error(e), id=call_item.serial
                )
        finally:
            self._call_later(
                self._CLEAN_LOCK_TIMEOUT, self.__clean_lock, call_item.serial
            )

    @staticmethod
    def _parse_message(data: dict) -> CallItem:
        message_id = data.get("id")  # type: t.Optional[int]

        if message_id and not isinstance(message_id, int):
            raise ValueError

        message_method: t.Union[str, Nothing, None] = data.get(
            "method", Nothing()
        )

        message_result: t.Union[str, Nothing, None] = data.get(
            "result", Nothing()
        )

        message_error: t.Union[str, Nothing, None] = data.get(
            "error", Nothing()
        )

        message_params: t.Union[
            t.List[t.Any], t.Dict[t.Any, t.Any], None
        ] = data.get("params", None)

        return CallItem(
            serial=message_id,
            method=message_method,
            result=message_result,
            error=message_error,
            params=message_params,
        )

    async def handle_message(self, message: aiohttp.WSMessage):
        # noinspection PyTypeChecker, PyNoneFunctionAssignment
        data: dict = message.json(loads=self._json_loads)
        log.debug("Got message: %r", data)

        serial = data.get("id")

        if serial is None:
            return await self.handle_event(data)

        call_item = self._parse_message(data)
        await self._call_method(call_item)

    async def _on_message(self, msg: aiohttp.WSMessage):
        async def unknown_method(msg: aiohttp.WSMessage):
            log.warning("Unhandled message %r %r", msg.type, msg.data)

        handler = self._message_type_mapping.get(msg.type, unknown_method)
        self._create_task(awaitable(handler)(msg))

    @classmethod
    def get_routes(cls) -> t.Dict[str, RouteType]:
        return cls._ROUTES[cls]

    @classmethod
    def get_clients(cls) -> t.Dict[str, AbstractWSRPC]:
        return cls._CLIENTS[cls]

    @property
    def routes(self) -> t.Dict[str, RouteType]:
        """Property which contains the socket routes"""
        return self.get_routes()

    @property
    def clients(self) -> t.Dict[str, AbstractWSRPC]:
        """Property which contains the socket clients"""
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

    def prepare_args(self, args):
        return self._prepare_args(args)

    @staticmethod
    def is_route(func):
        return hasattr(func, "__self__") and isinstance(func.__self__, Route)

    async def handle_method(self, method, serial, args, kwargs):
        await self.ON_CALL_START.call(
            method=method, serial=serial, args=args, kwargs=kwargs
        )
        callee = self.resolver(method)

        if not self.is_route(callee):
            a = [self]
            a.extend(args)
            args = a

        func = partial(callee, *args, **kwargs)
        try:
            result = await self._executor(func)
        except Exception as err:
            await self.ON_CALL_FAIL.call(
                method=method, serial=serial, args=args, kwargs=kwargs, err=err
            )
            raise

        await self.ON_CALL_SUCCESS.call(
            method=method,
            serial=serial,
            args=args,
            kwargs=kwargs,
            result=result,
        )

        await self._send(result=result, id=serial)

    async def handle_result(self, serial, result):
        cb = self._futures.pop(serial, None)
        if not cb or cb.done():
            return
        cb.set_result(result)

    async def handle_error(self, serial, error):
        self._reject(serial, error)
        log.error("Client return error: \n\t%r", error)

    def __clean_lock(self, serial):
        if serial not in self._locks:
            return
        log.debug("Release and delete lock for %s serial %s", self, serial)
        self._locks.pop(serial)

    async def handle_event(self, event):
        for listener in self._event_listeners:
            self._loop.call_soon(listener, event)

    @abc.abstractmethod
    async def _send(self, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _format_error(e):
        return {"type": str(type(e).__name__), "message": str(e)}

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
            func_name.split(".", 1) if "." in func_name else (func_name, "init")
        )

        callee = self.routes.get(class_name, self._unresolvable)

        if isinstance(callee, decorators.ProxyBase):
            callee = callee.func

        condition = (
            callee == self._unresolvable
            or isinstance(getattr(callee, "__self__", None), Route)
            or (
                not isinstance(callee, (types.FunctionType, types.MethodType))
                and issubclass(callee, Route)
            )
        )

        if condition:
            if class_name not in self._handlers:
                self._handlers[class_name] = callee(self)

            return self._handlers[class_name](method)

        callee = self.routes.get(func_name, self._unresolvable)
        if hasattr(callee, "__call__"):
            return callee
        else:
            raise NotImplementedError(
                "Method call of {0} is not implemented".format(repr(callee))
            )

    def _get_serial(self):
        self._serial += 2
        return self._serial

    async def call(self, func: str, timeout=None, **kwargs):
        """Method for call remote function

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

        log.info(
            'Sending request #%r "%s(%r)" to the client.', serial, func, kwargs
        )

        await self._send(**payload)
        result = await asyncio.wait_for(
            future, timeout=timeout or self._timeout
        )
        return result

    async def emit(self, event):
        await self._send(**event)

    @classmethod
    def add_route(cls, route: str, handler: RouteType) -> None:
        """Expose local function through RPC

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
        assert callable(handler) or isinstance(handler, Route)
        if callable(handler):
            handler = decorators.proxy(handler)

        cls.get_routes()[route] = handler

    def add_event_listener(self, func: EventListenerType):
        self._event_listeners.add(func)

    def remove_event_listeners(self, func):
        return self._event_listeners.remove(func)

    @classmethod
    def remove_route(cls, route: str, fail=True):
        """Removes route by name. If `fail=True` an exception
        will be raised in case the route was not found."""

        if fail:
            cls.get_routes().pop(route)
        else:
            cls.get_routes().pop(route, None)

    def __repr__(self):
        if hasattr(self, "id"):
            return "<RPCWebSocket: ID[{0}]>".format(self.id)
        else:
            return "<RPCWebsocket: {0} (waiting)>".format(self.__hash__())

    @abc.abstractmethod
    async def _executor(self, func):
        raise NotImplementedError

    @property
    def proxy(self):
        """Special property which allow run the remote functions
        by `dot` notation

        .. code-block:: python

            # calls remote function with name ping
            await client.proxy.ping()

            # full equivalent of
            await client.call('ping')
        """
        return Proxy(self.call)


__all__ = ("Route", "WSRPCBase", "ClientException", "WSRPCError")
