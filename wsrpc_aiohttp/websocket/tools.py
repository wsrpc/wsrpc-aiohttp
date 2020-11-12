import asyncio
import base64
from functools import singledispatch, wraps
from json import dumps as _dumps


try:
    from ujson import loads     # type: ignore
except ImportError:
    from json import loads      # type: ignore


class Lazy:
    __slots__ = ("func",)

    def __init__(self, func):
        self.func = func

    def __str__(self):
        return str(self.func())

    def __repr__(self):
        return repr(self.func())


@singledispatch
def serializer(value):
    """ singledispatch wrapped function.
    You might register custom types if you want pass it to the remote side.

    .. code-block:: python

        from wsrpc_aiohttp import serializer

        class MyObject:
            def __init__(self):
                self.foo = 'bar'

        @serializer.register(MyObject)
        def _(value: MyObject) -> dict:
            return {'myObject': {'foo': value.foo}}
    """
    raise ValueError("Can not serialize %r" % type(value))


@serializer.register(bytes)  # noqa: W0404
def _(value):
    return base64.b64encode(value).decode()


def dumps(obj):
    return _dumps(obj, default=serializer)


class SingletonMeta(type):
    def __new__(cls, clsname, superclasses, attributedict):
        klass = type.__new__(cls, clsname, superclasses, attributedict)
        klass.__instance__ = None
        return klass


class Singleton(metaclass=SingletonMeta):
    def __new__(cls, *args, **kwargs):
        if not cls.__instance__:
            cls.__instance__ = super(Singleton, cls).__new__(cls)
        return cls.__instance__


def awaitable(func):
    if asyncio.iscoroutinefunction(func):
        return func

    @wraps(func)
    async def wrap(*args, **kwargs):
        result = func(*args, **kwargs)

        is_awaitable = (
            asyncio.iscoroutine(result)
            or asyncio.isfuture(result)
            or hasattr(result, "__await__")
        )
        if is_awaitable:
            return await result
        return result

    return wrap


__all__ = (
    "Lazy",
    "Singleton",
    "awaitable",
    "dumps",
    "loads",
)
