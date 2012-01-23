# -*- coding: utf-8 -*-
#
#  File:       collab.py
#  Author:     Juan Pedro Bolívar Puente <raskolnikov@es.gnu.org>
#  Date:       Fri Jan 20 15:49:30 2012
#  Time-stamp: <2012-01-23 19:42:08 jbo>
#

#
#  Copyright (C) 2012 Juan Pedro Bolívar Puente
#
#  This file is part of jpblib.
#
#  jpblib is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  jpblib is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


"""
Cooperative methods helper library.
"""

import inspect
from functools import wraps

class CooperativeError(Exception): pass
class ConstructorError(CooperativeError):  pass

def check_is_constructor(method):
    if method.__name__ != '__init__':
        raise ConstructorError

def check_all_params_are_keyword(method):
    """
    Raises ConstructorError if method any parameter that is not a
    named keyword parameter
    """

    args, varargs, keywords, defaults = inspect.getargspec(method)

    # Always have self, thus the -1
    if len(args or []) - 1 != len(defaults or []):
        raise ConstructorError, "Constructor has positional parameters " + \
              str(args[1:])
    if varargs:
        raise ConstructorError, "Constructor has variadic positional parameters"
    if keywords:
        raise ConstructorError, "Constructor has variadic keyword parameters"

def extract_keywords(method, keys):
    """
    Removes all keyword parameters required by 'method' from
    dictionary 'keys' and returns them in a separate dictionary.
    """

    args, _1, _2, defs = inspect.getargspec(method)
    defs = defs or []
    new = {}
    for a, d in zip(args[-len(defs):], defs):
        if a in keys:
            new[a] = keys[a]
            del keys[a]
    return new

def constructor(cls):
    def decorator(method):
        check_is_constructor(method)
        check_all_params_are_keyword(method)
        @wraps(method)
        def wrapper(self, **orig):
            ours = extract_keywords(method, orig)
            super(cls, self).__init__(**orig)
            method(self, **ours)
        return wrapper
    return decorator

def defines_method(cls, method_name):
    deriv_method = getattr(getattr(cls, method_name, None), 'im_func', None)
    super_method = getattr(getattr(super(cls, cls), method_name, None), 'im_func', None)
    return id(super_method) != id(deriv_method)


def cooperative(cls):
    if defines_method(cls, '__init__'):
        wrapped_constructor = constructor(cls)(cls.__dict__['__init__'])
        wrapped_constructor.__objclass__ = cls
        cls.__init__ = wrapped_constructor
    return cls


class CooperativeMeta(type):
    def __init__(cls, name, bases, dct):
        super(CooperativeMeta, cls).__init__(name, bases, dct)
        cooperative(cls)
