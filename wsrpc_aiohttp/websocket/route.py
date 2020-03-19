import logging

import asyncio
from . import handler       # noqa

log = logging.getLogger("wsrpc")


class decorators:

    _PROXY_ATTR = '__wsrpc_aiohttp_proxy__'

    @staticmethod
    def proxy(f):
        setattr(f, decorators._PROXY_ATTR, True)
        return f

    @staticmethod
    def is_proxied(f):
        return getattr(f, decorators._PROXY_ATTR, False)


class WebSocketRoute(object):

    def __init__(self, obj: 'handler.WebSocketBase'):
        self.socket = obj

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.socket._loop    # noqa

    def _resolve(self, method):
        if method.startswith('_'):
            raise AttributeError('Trying to get private method.')

        if hasattr(self, method):
            func = getattr(self, method)
            if decorators.is_proxied(func):
                raise NotImplementedError('Method not implemented')
            else:
                return func
        else:
            raise NotImplementedError('Method not implemented')

    def _onclose(self):
        pass

    @classmethod
    def placebo(*args, **kwargs):
        log.debug("PLACEBO IS CALLED!!! args: %r, kwargs: %r", args, kwargs)


__all__ = 'WebSocketRoute',
