import base64
from functools import singledispatch
from json import dumps as _dumps


try:
    from ujson import loads
except ImportError:
    from json import loads


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


__all__ = ("dumps", "loads", "Lazy", "Singleton")
