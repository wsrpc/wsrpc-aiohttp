import asyncio
import logging
from types import MappingProxyType

from . import decorators


log = logging.getLogger("wsrpc")


# noinspection PyUnresolvedReferences
class RouteMeta(type):
    def __new__(cls, clsname, superclasses, attributedict):
        attrs = {"__no_proxy__": set(), "__proxy__": set()}

        for key, value in attributedict.items():
            if key in ("__proxy__", "__no_proxy__"):
                continue
            if isinstance(value, decorators.NoProxyFunction):
                if isinstance(value, decorators.ProxyBase):
                    value = value.func
                attrs["__no_proxy__"].add(key)
            elif isinstance(value, decorators.ProxyFunction):
                if isinstance(value, decorators.ProxyBase):
                    value = value.func
                attrs["__proxy__"].add(key)

            attrs[key] = value

        instance = type.__new__(cls, clsname, superclasses, attrs)

        for key, value in attrs.items():
            if not callable(value):
                continue

            if isinstance(value, decorators.ProxyBase):
                value = value.func

            if instance.__is_method_allowed__(key, value) is True:
                instance.__proxy__.add(key)
            elif instance.__is_method_masked__(key, value) is True:
                instance.__no_proxy__.add(key)

        for key in ("__no_proxy__", "__proxy__"):
            setattr(instance, key, frozenset(getattr(instance, key)))

        return instance


class RouteBase(metaclass=RouteMeta):
    __proxy__ = MappingProxyType({})
    __no_proxy__ = MappingProxyType({})

    def __init__(self, obj):
        self.socket = obj

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.socket._loop  # noqa

    def _onclose(self):
        pass

    @classmethod
    def __is_method_allowed__(cls, name, func):
        return None

    @classmethod
    def __is_method_masked__(cls, name, func):
        return None


class Route(RouteBase):
    def _method_lookup(self, method):
        if method in self.__no_proxy__:
            return

        if method in self.__proxy__:
            return getattr(self, method)

    def _resolve(self, method):
        if method.startswith("_") or method in self.__no_proxy__:
            raise AttributeError("Trying to get private method.")

        func = self._method_lookup(method)
        if func is not None:
            return func

        raise NotImplementedError("Method not implemented")

    @decorators.proxy
    def placebo(self, *args, **kwargs):
        log.debug("PLACEBO IS CALLED!!! args: %r, kwargs: %r", args, kwargs)


class AllowedRoute(Route):
    @classmethod
    def __is_method_allowed__(cls, name, func):
        if name.startswith("_"):
            return False
        return True


class PrefixRoute(Route):
    PREFIX = "rpc_"

    @classmethod
    def __is_method_allowed__(cls, name, func):
        if name.startswith("rpc_"):
            return True
        return False

    def _method_lookup(self, method):
        return super()._method_lookup(self.PREFIX + method)


class WebSocketRoute(AllowedRoute):
    @classmethod
    def noproxy(cls, func):
        return decorators.noproxy(func)


__all__ = (
    "RouteBase",
    "Route",
    "WebSocketRoute",
    "AllowedRoute",
    "decorators",
)
