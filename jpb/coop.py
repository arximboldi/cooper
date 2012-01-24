# -*- coding: utf-8 -*-
#
#  File:       collab.py
#  Author:     Juan Pedro Bolívar Puente <raskolnikov@es.gnu.org>
#  Date:       Fri Jan 20 15:49:30 2012
#  Time-stamp: <2012-01-24 12:27:51 jbo>
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
class InitError(CooperativeError):  pass


def check_is_init(method):
    if method.__name__ != '__init__':
        raise InitError


def check_all_params_are_keyword(method):
    """
    Raises InitError if method any parameter that is not a
    named keyword parameter
    """

    args, varargs, keywords, defaults = inspect.getargspec(method)

    # Always have self, thus the -1
    if len(args or []) - 1 != len(defaults or []):
        raise InitError, "Init has positional parameters " + \
              str(args[1:])
    if varargs:
        raise InitError, "Init has variadic positional parameters"
    if keywords:
        raise InitError, "Init has variadic keyword parameters"


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


def decorate_init(cls, fixed_keywords={}):
    def decorator(method):
        check_is_init(method)
        check_all_params_are_keyword(method)
        @wraps(method)
        def wrapper(self, **orig):
            ours = extract_keywords(method, orig)
            orig.update(fixed_keywords)
            super(cls, self).__init__(**orig)
            method(self, **ours)
        return wrapper
    return decorator


class InitDecorator(object):
    """
    An init decorator will take a init function in its constructor and
    should return the decorated version when called with the class as
    a parameter.
    """
    def __call__(self, cls):
        pass


class manual_init(InitDecorator):
    def __init__(self, function=None, *a, **k):
        super(manual_init, self).__init__(*a, **k)
        self.wrapped_init = function
    def __call__(self, cls):
        return self.wrapped_init


def super_params(**keywords):
    class FixedInit(InitDecorator):
        def __init__(self, function=None, *a, **k):
            super(FixedInit, self).__init__(*a, **k)
            self.wrapped_init = function
        def __call__(self, cls):
            decorator = decorate_init(cls, fixed_keywords=keywords)
            return decorator(self.wrapped_init)
    return FixedInit


def defines_method(cls, method_name):
    deriv_method = getattr(getattr(cls, method_name, None), 'im_func', None)
    super_method = getattr(getattr(super(cls, cls), method_name, None), 'im_func', None)
    return id(super_method) != id(deriv_method)


def cooperative(cls):
    if hasattr(cls, '_cooperative_classes_set'):
        coops = cls._cooperative_classes_set
        if cls in coops:
            # Already decorated, maybe mixing Meta and decorator
            return cls
    else:
        if cls.__mro__[1:] != (object,):
            raise CooperativeError, "Subclasses are not cooperative."
        cls._cooperative_classes_set = set()

    if defines_method(cls, '__init__'):
        init = cls.__dict__['__init__']
        if isinstance(init, InitDecorator):
            wrapped_init = init(cls)
        else:
            wrapped_init = decorate_init(cls)(init)
        wrapped_init.__objclass__ = cls
        cls.__init__ = wrapped_init
    return cls


class CooperativeMeta(type):
    def __init__(cls, name, bases, dct):
        super(CooperativeMeta, cls).__init__(name, bases, dct)
        cooperative(cls)
