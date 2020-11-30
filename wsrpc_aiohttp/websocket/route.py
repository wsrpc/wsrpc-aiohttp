import asyncio
import logging
from abc import ABCMeta
from types import MappingProxyType
from typing import Any, Callable, Mapping

from . import decorators
from .abc import AbstractRoute, AbstractWebSocket

log = logging.getLogger("wsrpc")


# noinspection PyUnresolvedReferences
class RouteMeta(ABCMeta):
    def __new__(cls, clsname, superclasses, attributedict):
        attrs = {"__no_proxy__": set(), "__proxy__": set()}

        for superclass in superclasses:
            if not hasattr(superclass, "__proxy__"):
                continue

            attrs["__no_proxy__"].update(superclass.__no_proxy__)
            attrs["__proxy__"].update(superclass.__proxy__)

        for key, value in attributedict.items():
            if key in ("__proxy__", "__no_proxy__"):
                continue
            if isinstance(value, decorators.NoProxyFunction):
                value = value.func
                attrs["__no_proxy__"].add(key)
            elif isinstance(value, decorators.ProxyFunction):
                value = value.func
                attrs["__proxy__"].add(key)

            attrs[key] = value

        instance = super(RouteMeta, cls).__new__(
            cls, clsname, superclasses, attrs
        )

        for key, value in attrs.items():
            if not callable(value):
                continue

            if instance.__is_method_allowed__(key, value) is True:
                instance.__proxy__.add(key)
            elif instance.__is_method_masked__(key, value) is True:
                instance.__no_proxy__.add(key)

        for key in ("__no_proxy__", "__proxy__"):
            setattr(instance, key, frozenset(getattr(instance, key)))

        return instance


ProxyCollectionType = Mapping[str, Callable[..., Any]]


class RouteBase(AbstractRoute, metaclass=RouteMeta):
    __proxy__ = MappingProxyType({})        # type: ProxyCollectionType
    __no_proxy__ = MappingProxyType({})     # type: ProxyCollectionType

    def __init__(self, socket: AbstractWebSocket):
        super().__init__(socket)
        self.__socket = socket
        self.__loop = getattr(self.socket, "_loop", None)

        if self.__loop is None:
            self.__loop = asyncio.get_event_loop()

    @property
    def socket(self) -> AbstractWebSocket:
        return self.__socket

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.__loop

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
            raise NotImplementedError("Method masked")

        if method in self.__proxy__:
            return getattr(self, method)

        raise NotImplementedError("Method not implemented")

    @classmethod
    def __is_method_masked__(cls, name, func):
        if name.startswith("_"):
            return True

    def __call__(self, method):
        return self._method_lookup(method)


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
