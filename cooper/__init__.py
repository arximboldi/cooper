# -*- coding: utf-8 -*-
#
#  File:       __init__.py
#  Author:     Juan Pedro Bolívar Puente <raskolnikov@es.gnu.org>
#  Date:       Fri Jan 20 15:49:30 2012
#

#
#  Copyright (c) 2012, 2015 Juan Pedro Bolivar Puente <raskolnikov@gnu.org>
#
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, including without limitation the rights to use, copy,
#  modify, merge, publish, distribute, sublicense, and/or sell copies
#  of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#

"""
Cooperative methods helper library.
"""

import inspect
from functools import wraps

class CooperativeError(TypeError): pass

def check_no_params(method):
    if any(inspect.getargspec(method)):
        raise CooperativeError, "Del has parameters."

def check_all_params_are_keyword(method):
    """
    Raises CooperativeError if method any parameter that is not a
    named keyword parameter
    """

    args, varargs, keywords, defaults = inspect.getargspec(method)

    # Always have self, thus the -1
    if len(args or []) - 1 != len(defaults or []):
        raise CooperativeError, "Init has positional parameters " + \
              str(args[1:])
    if varargs:
        raise CooperativeError, "Init has variadic positional parameters"
    if keywords:
        raise CooperativeError, "Init has variadic keyword parameters"

def has_keywords(method):
    return bool(inspect.getargspec(method)[3])

def make_keyword_extractor(method):
    """
    Removes all keyword parameters required by 'method' from
    dictionary 'keys' and returns them in a separate dictionary.
    """

    args, _1, _2, defs = inspect.getargspec(method)
    key_args = args[-len(defs or []):]
    def extractor(keys):
        new = {}
        for a in key_args:
            if a in keys:
                new[a] = keys[a]
                del keys[a]
        return new
    return extractor

def decorate_cooperating(cls, method,
                         fixed_keywords  = {},
                         post_cooperate  = False,
                         inner_cooperate = False):
    # TODO: Cleanup this function is too big!

    assert not post_cooperate or \
           not inner_cooperate

    method_name = method.__name__

    if method_name == '__init__':
        check_all_params_are_keyword(method)
    if method_name == '__del__':
        check_no_params(method)

    extractor = make_keyword_extractor(method)

    if post_cooperate:
        if has_keywords(method) or fixed_keywords:
            def wrapper(self, *a, **orig):
                ours = extractor(orig)
                orig.update(fixed_keywords)
                method(self, *a, **ours)
                return getattr(super(cls, self), method_name)(*a, **orig)
        else:
            def wrapper(self, *a, **orig):
                method(self, *a)
                return getattr(super(cls, self), method_name)(*a, **orig)

    elif inner_cooperate:
        assert not fixed_keywords
        # TODO: Maybe disregard this check for the sake of
        # performance or some other patterns.
        inner_call_count = [0]
        def wrapper(self, *a, **orig):
            ours = extractor(orig)
            orig.update(fixed_keywords)
            next_fn = getattr(super(cls, self), method_name)
            def next_method(**kws):
                inner_call_count[0] += 1
                orig.update(kws)
                next_fn(*a, **orig)
            result = method(self, next_method, *a, **ours)
            if inner_call_count[0] != 1:
                raise CooperativeError, "Next method must be called exactly once."
            inner_call_count[0] = 0
            return result

    else:
        if has_keywords(method) or fixed_keywords:
            def wrapper(self, *a, **orig):
                ours = extractor(orig)
                orig.update(fixed_keywords)
                getattr(super(cls, self), method_name)(*a, **orig)
                return method(self, *a, **ours)
        else:
            def wrapper(self, *a, **orig):
                getattr(super(cls, self), method_name)(*a, **orig)
                return method(self, *a)

    wrapper = wraps(method)(wrapper)
    wrapper.__objclass__ = cls
    return wrapper


class CoopDecorator(object):
    """
    A coop decorator will take a init function in its constructor and
    should return the decorated version when called with the class as
    a parameter.
    """
    def __init__(self, function=None, *a, **k):
        super(CoopDecorator, self).__init__(*a, **k)
        self.wrapped_function = function

    def __call__(self, cls):
        return decorate_cooperating(cls, self.wrapped_function)


class cooperative(CoopDecorator):
    def __call__(self, cls):
        raise CooperativeError, "Cooperative method should not override"

class abstract(cooperative):
    """ Compatible with abc.abstractmethod and related classes """
    def __init__(self, function=None, *a, **k):
        super(CoopDecorator, self).__init__(*a, **k)
        self.wrapped_function = function
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True

class cooperate(CoopDecorator):
    pass

class post_cooperate(CoopDecorator):
    def __call__(self, cls):
        return decorate_cooperating(cls, self.wrapped_function,
                                    post_cooperate = True)

class inner_cooperate(CoopDecorator):
    def __call__(self, cls):
        return decorate_cooperating(cls, self.wrapped_function,
                                    inner_cooperate = True)

class manual_cooperate(CoopDecorator):
    def __call__(self, cls):
        return self.wrapped_function

def cooperate_with_params(**keywords):
    class FixedParams(CoopDecorator):
        def __call__(self, cls):
            return decorate_cooperating(cls, self.wrapped_function,
                                        fixed_keywords = keywords)
    return FixedParams

def post_cooperate_with_params(**keywords):
    class FixedParams(CoopDecorator):
        def __call__(self, cls):
            return decorate_cooperating(cls, self.wrapped_function,
                                        fixed_keywords = keywords,
                                        post_cooperate = True)
    return FixedParams


def defines_method(cls, method_name):
    return method_name in cls.__dict__

def overrides_method(cls, method_name):
    return method_name in cls.__dict__ and \
           hasattr(super(cls, cls), method_name)

def overrides_cooperative(cls, method_name):
    return is_cooperative(getattr(super(cls, cls), method_name, None))

def is_cooperative(cls_or_fn):
    return getattr(cls_or_fn, '_cooperative_is_coop', False)


def check_cooperative_bases(cls):
    bases = cls.__bases__
    good  = len(bases) == 1 or all(map(is_cooperative, bases))
    if not good:
        raise CooperativeError, "Can not multiple-inherit non cooperative."


def get_abstract_methods(cls):
    return filter(lambda x: getattr(x, '__isabstractmethod__', False),
                  cls.__dict__.itervalues())


def check_single_root(cls, name):
    # TODO: Do full method override checking at least in debug mode.
    basic = filter(lambda c: getattr(getattr(c, name, None),
                                     '_cooperative_is_root', False),
                   cls.__mro__)
    if len(basic) > 1:
        raise CooperativeError, \
              "Cooperative method (" + name + ") has conflicting declarations."


def decorate_cooperative_methods(cls):
    for name, value in cls.__dict__.iteritems():
        if name != '__init__':
            check_single_root(cls, name)
            if isinstance(value, CoopDecorator):
                if overrides_method(cls, name):
                    wrapped = value(cls)
                else:
                    wrapped = value.wrapped_function
                    wrapped._cooperative_is_root = True
                wrapped._cooperative_is_coop = True
                setattr(cls, name, wrapped)
            elif overrides_cooperative(cls, name):
                # TODO: This enforces explicit cooperation. This
                # contradicts behaviour for __init__. Should we make
                # this consistent either by making it optionally
                # implicit or enforcing it explicity for __init__
                raise CooperativeError, \
                      "Overriding cooperative method without cooperation"


def decorate_init(cls):
    if defines_method(cls, '__init__'):
        init = cls.__dict__['__init__']
        if isinstance(init, CoopDecorator):
            wrapped_init = init(cls)
        else:
            raise CooperativeError, \
                  "Constructor should cooperate in cooperative class"
        cls.__init__ = wrapped_init

def decorate_del(cls):
    if defines_method(cls, '__del__'):
        fin = cls.__dict__['__del__']
        if isinstance(fin, CoopDecorator):
            wrapped_fin = fin(cls)
        else:
            raise CooperativeError, \
                  "Finalizer should cooperate in cooperative class"
        cls.__del__ = wrapped_fin


def cooperative_class(cls):
    check_cooperative_bases(cls)
    cls.__abstractmethods__ = frozenset(get_abstract_methods(cls))
    decorate_init(cls)
    decorate_del(cls)
    decorate_cooperative_methods(cls)
    cls._cooperative_is_coop = True
    return cls

class CooperativeMeta(type):
    def __init__(cls, name, bases, dct):
        super(CooperativeMeta, cls).__init__(name, bases, dct)
        cooperative_class(cls)

class Cooperative(object):
    __metaclass__ = CooperativeMeta
