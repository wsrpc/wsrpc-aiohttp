import inspect
import logging
from collections.abc import Callable, Coroutine
from typing import Any, Generic, ParamSpec

P = ParamSpec("P")

log = logging.getLogger(__name__)


class Signal(Generic[P]):
    __slots__ = ("_receivers", "_is_frozen")

    def __init__(self) -> None:
        self._receivers: (
            set[Callable[P, Coroutine[Any, Any, Any]]]
            | frozenset[Callable[P, Coroutine[Any, Any, Any]]]
        ) = set()

    def connect(self, receiver: Callable[P, Coroutine[Any, Any, Any]]) -> None:
        if isinstance(self._receivers, frozenset):
            raise RuntimeError(
                "Can't connect receiver (%r) to the frozen signal", receiver
            )

        if not inspect.iscoroutinefunction(receiver):
            raise RuntimeError("%r is not a coroutine function", receiver)

        self._receivers.add(receiver)

    async def call(self, *args: P.args, **kwargs: P.kwargs) -> None:
        for receiver in self._receivers:
            try:
                await receiver(*args, **kwargs)
            except Exception:
                log.exception("Exception in signal handler")

    def copy(self) -> "Signal[P]":
        clone: Signal[P] = Signal()
        # unfreeze on copy
        clone._receivers = set(self._receivers)
        return clone

    @property
    def is_frozen(self) -> bool:
        return isinstance(self._receivers, frozenset)

    def freeze(self) -> None:
        self._receivers = frozenset(self._receivers)


def receiver(
    s: Signal[P],
) -> Callable[
    [Callable[P, Coroutine[Any, Any, Any]]],
    Callable[P, Coroutine[Any, Any, Any]],
]:
    def decorator(
        func: Callable[P, Coroutine[Any, Any, Any]],
    ) -> Callable[P, Coroutine[Any, Any, Any]]:
        s.connect(func)
        return func

    return decorator
