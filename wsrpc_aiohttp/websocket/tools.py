try:
    import ujson as json
except ImportError:
    import json


class Lazy(object):
    def __init__(self, func):
        self.func = func

    def __str__(self):
        return self.func()


__all__ = ('json', 'Lazy')
