import base64
import inspect
import json
from collections.abc import Awaitable, Callable, Coroutine
from functools import singledispatch, wraps
from typing import Any, ClassVar, Generic, ParamSpec, TypeVar, cast, overload

P = ParamSpec("P")
T = TypeVar("T")


class Lazy(Generic[T]):
    __slots__ = ("func",)

    def __init__(self, func: Callable[[], T]) -> None:
        self.func = func

    def __str__(self) -> str:
        return str(self.func())

    def __repr__(self) -> str:
        return repr(self.func())


@singledispatch
def serializer(value):
    """singledispatch wrapped function.
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
    raise ValueError(f"Can not serialize {type(value)!r}")


@serializer.register(bytes)  # noqa: W0404
def _(value):
    return base64.b64encode(value).decode()


def json_dumps(value: Any, **kwargs: Any) -> str:
    """Encode JSON using registered serializers unless default is overridden."""
    kwargs.setdefault("default", serializer)
    return json.dumps(value, **kwargs)


class SingletonMeta(type):
    def __new__(cls, clsname, superclasses, attributedict):
        klass: Any = type.__new__(cls, clsname, superclasses, attributedict)
        klass.__instance__ = None
        return klass


class Singleton(metaclass=SingletonMeta):
    __instance__: ClassVar[Any] = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance__:
            cls.__instance__ = super().__new__(cls)
        return cls.__instance__


@overload
def awaitable(
    func: Callable[P, Awaitable[T]],
) -> Callable[P, Coroutine[Any, Any, T]]: ...


@overload
def awaitable(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]: ...


def awaitable(func: Callable[P, Any]) -> Callable[P, Coroutine[Any, Any, Any]]:
    if inspect.iscoroutinefunction(func):
        return cast(Callable[P, Coroutine[Any, Any, Any]], func)

    @wraps(func)
    async def wrap(*args: P.args, **kwargs: P.kwargs) -> Any:
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    return wrap


__all__ = ("Lazy", "Singleton", "awaitable", "json_dumps", "serializer")
