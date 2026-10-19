from collections.abc import Callable
from functools import partial
from typing import ParamSpec, TypeVar, cast

P = ParamSpec("P")
T = TypeVar("T")


class ProxyBase(partial):
    pass


class NoProxyFunction(ProxyBase):
    pass


class ProxyFunction(ProxyBase):
    pass


def noproxy(func: Callable[P, T]) -> Callable[P, T]:
    return cast(Callable[P, T], NoProxyFunction(func))


def proxy(func: Callable[P, T]) -> Callable[P, T]:
    return cast(Callable[P, T], ProxyFunction(func))
