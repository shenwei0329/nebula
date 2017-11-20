class Proxy(object):
    __slots__ = ['_obj']

    def __init__(self, obj):
        self.set_obj(obj)

    def set_obj(self, obj):
        object.__setattr__(self, '_obj', obj)

    def __getattr__(self, attr):
        return getattr(self._obj, attr)

    def __setattr__(self, attr, val):
        return setattr(self._obj, attr, val)

    def __delattr__(self, attr):
        return delattr(self._obj, attr)

    def __call__(self, *args, **kw):
        return self._obj(*args, **kw)
