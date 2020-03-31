from functools import partial


class ProxyBase(partial):
    pass


class NoProxyFunction(ProxyBase):
    pass


class ProxyFunction(ProxyBase):
    pass


def noproxy(func):
    return NoProxyFunction(func)


def proxy(func):
    return ProxyFunction(func)
