from functools import singledispatch

try:
    import ujson as json
except ImportError:
    import json


class Lazy(object):
    def __init__(self, func):
        self.func = func

    def __str__(self):
        return self.func()


@singledispatch
def serializer(value):
    raise ValueError("Can't serialize %r" % type(value))


@serializer.register(tuple)     # noqa: W0404
@serializer.register(list)
def _(value):
    return [serializer(i) for i in value]


@serializer.register(dict)      # noqa: W0404
def _(value):
    result = dict()
    for key, value in value.items():
        result[serializer(key)] = serializer(value)

    return result


@serializer.register(int)       # noqa: W0404
@serializer.register(float)
@serializer.register(str)
@serializer.register(type(None))
@serializer.register(bool)
def _(value):
    return value


@serializer.register(bytes)     # noqa: W0404
def _(value):
    return value.decode()


__all__ = ('json', 'Lazy')
