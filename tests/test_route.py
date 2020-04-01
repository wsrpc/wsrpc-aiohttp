from unittest.mock import Mock

from wsrpc_aiohttp import Route, decorators


def test_meta():
    class MyRoute(Route):
        pass

    assert MyRoute.__proxy__ is not None
    assert MyRoute.__no_proxy__ is not None


def test_inheritance():
    class BaseRoute(Route):
        @decorators.proxy
        def count(self):
            return 0

    class Mixin:
        def foo(self):
            pass

    class UserRoute(BaseRoute):
        pass

    class RoleRoute(BaseRoute, Mixin):
        @decorators.noproxy
        def masked(self):
            return 42

    class ChildRoleRoute(RoleRoute):
        pass

    assert UserRoute.__proxy__
    assert RoleRoute.__proxy__
    assert ChildRoleRoute.__proxy__
    assert "foo" not in RoleRoute.__proxy__
    assert "foo" not in RoleRoute.__no_proxy__
    assert "masked" in RoleRoute.__no_proxy__
    assert "masked" in ChildRoleRoute.__no_proxy__


def test_is_method_masked():
    class FooMaskedRoute(Route):
        @classmethod
        def __is_method_masked__(cls, name, func):
            if name.startswith("foo_"):
                return True

    class MyRoute(FooMaskedRoute):
        pass

    class FooRoute(MyRoute):
        def foo_one(self):
            pass

        def foo_two(self):
            pass

        def foobar(self):
            pass

    assert "foo_one" in FooRoute.__no_proxy__
    assert "foo_one" not in FooRoute.__proxy__

    assert "foo_two" in FooRoute.__no_proxy__
    assert "foo_two" not in FooRoute.__proxy__

    assert "foobar" not in FooRoute.__no_proxy__
    assert "foobar" not in FooRoute.__proxy__


def test_is_method_allowed():
    class FooMaskedRoute(Route):
        @classmethod
        def __is_method_allowed__(cls, name, func):
            if name.startswith("foo_"):
                return True

    class MyRoute(FooMaskedRoute):
        pass

    class FooRoute(MyRoute):
        def foo_one(self):
            pass

        def foo_two(self):
            pass

        def foobar(self):
            pass

    assert "foo_one" in FooRoute.__proxy__
    assert "foo_one" not in FooRoute.__no_proxy__

    assert "foo_two" in FooRoute.__proxy__
    assert "foo_two" not in FooRoute.__no_proxy__

    assert "foobar" not in FooRoute.__proxy__
    assert "foobar" not in FooRoute.__no_proxy__


def test_route__init__(loop):
    socket = Mock()
    socket._loop = object()

    route = Route(socket)

    assert route.socket is socket
    assert route.loop is socket._loop

    socket = object()
    route = Route(socket)

    assert route.socket is socket
    assert route.loop is loop
