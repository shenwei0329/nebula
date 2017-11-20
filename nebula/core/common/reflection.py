# -*- coding: utf-8 -*-
"""Reflection related utilities, stolen from  taskfow.utils.reflection"""
import inspect

import six


def get_callable_name(function):
    """Generate a name from callable.

    Tries to do the best to guess fully qualified callable name.
    """
    method_self = get_method_self(function)
    if method_self is not None:
        # this is bound method
        if isinstance(method_self, six.class_types):
            # this is bound class method
            im_class = method_self
        else:
            im_class = type(method_self)
        parts = (im_class.__module__, im_class.__name__,
                 function.__name__)
    elif inspect.isfunction(function) or inspect.ismethod(function):
        parts = (function.__module__, function.__name__)
    else:
        im_class = type(function)
        if im_class is type:
            im_class = function
        parts = (im_class.__module__, im_class.__name__)
    return '.'.join(parts)


def get_method_self(method):
    if not inspect.ismethod(method):
        return None
    try:
        return six.get_method_self(method)
    except AttributeError:
        return None


def get_fullname_of_class(cls):
    module = cls.__module__
    if module is None or module == '__builtin__':
        return cls.__name__
    return '%s.%s' % (module, cls.__name__)
