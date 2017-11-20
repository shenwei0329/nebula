# -*- coding: utf-8 -*-


def table_args(*args):
    """Merges __table_args__ from one or more declarative mixins with
    the given table_args argument."""

    positional_args = []
    dict_args = {}

    def _merge(ta):
        if isinstance(ta, dict):
            dict_args.update(ta)
        else:
            last = ta[-1]
            if isinstance(last, dict):
                positional_args.extend(ta[:-1])
                dict_args.update(ta[-1])
            else:
                positional_args.extend(ta)

    # Start by adding in our own table_args
    _merge(args)

    def wrapper(cls):
        # Now walk through the inheritance hierarchy
        bases = cls.__mro__[1:]
        for base in bases:
            if hasattr(base, '__table_args__'):
                _merge(cls.__table_args__)
        positional_args.append(dict_args)
        return tuple(positional_args)

    return wrapper
