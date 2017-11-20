# -*- coding: utf-8 -*-
import re

_SNAKE_CASIFY_PHASE1_RE = re.compile(r'(.)([A-Z][a-z]+)')
_SNAKE_CASIFY_PHASE2_RE = re.compile(r'([a-z0-9])([A-Z])')


def snake_casify(name):
    s1 = _SNAKE_CASIFY_PHASE1_RE.sub(r'\1_\2', name)
    return _SNAKE_CASIFY_PHASE2_RE.sub(r'\1_\2', s1).lower()
