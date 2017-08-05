import asyncio

try:
    import ujson as json
except ImportError:
    import json


class Lazy(object):
    def __init__(self, func):
        self.func = func

    def __str__(self):
        return self.func()


def future_with_timeout(timeout, loop: asyncio.AbstractEventLoop):
    future = loop.create_future()      # type: asyncio.Future


    return future
