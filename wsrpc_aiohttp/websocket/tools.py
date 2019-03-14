import base64
from functools import singledispatch

from json import dumps as _dumps

try:
    from ujson import loads
except ImportError:
    from json import loads


class Lazy:
    __slots__ = 'func',

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


@serializer.register(bytes)     # noqa: W0404
def _(value):
    return base64.b64encode(value).decode()


def dumps(obj):
    return _dumps(obj, default=serializer)


__all__ = ('dumps', 'loads', 'Lazy')
