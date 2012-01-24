# -*- coding: utf-8 -*-
#
#  File:       jpb_coop.py
#  Author:     Juan Pedro Bolívar Puente <raskolnikov@es.gnu.org>
#  Date:       Fri Jan 20 16:12:23 2012
#  Time-stamp: <2012-01-24 12:58:43 jbo>
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
Tests for jpb.coop
"""

from jpb import coop
from itertools import repeat

import unittest


def make_test_hierarchy(trace, decorator=lambda x:x, metacls=type):

    @decorator
    class _A(object):
        __metaclass__ = metacls
        def __init__(self):
            trace.append(_A.__init__)
    @decorator
    class _B(_A):
        __metaclass__ = metacls
        def __init__(self, b_param = 'b_param'):
            self._b_param = b_param
            trace.append(_B.__init__)
    @decorator
    class _C(_A):
        __metaclass__ = metacls
        def __init__(self):
            trace.append(_C.__init__)
    @decorator
    class _D(_B, _C):
        __metaclass__ = metacls
        def __init__(self, d_param = 'd_param'):
            self._d_param = d_param
            trace.append(_D.__init__)
    @decorator
    class _F(_D, _A):
        __metaclass__ = metacls

    return _A, _B, _C, _D, _F


class TestCoop(unittest.TestCase):

    cls_decorator = coop.cooperative
    cls_meta      = type

    def setUp(self):
        self._trace = []
        self._A, self._B, self._C, self._D, self._F = make_test_hierarchy(
            self._trace,
            decorator = self.cls_decorator.im_func,
            metacls   = self.cls_meta)

    def test_init_parameter_passing(self):
        obj = self._D()
        self.assertEqual(obj._b_param, 'b_param')
        self.assertEqual(obj._d_param, 'd_param')
        obj = self._D(b_param = 'new_b_param')
        self.assertEqual(obj._b_param, 'new_b_param')
        self.assertEqual(obj._d_param, 'd_param')
        obj = self._D(d_param = 'new_d_param')
        self.assertEqual(obj._b_param, 'b_param')
        self.assertEqual(obj._d_param, 'new_d_param')
        obj = self._D(d_param = 'new_d_param',
                 b_param = 'new_b_param')
        self.assertEqual(obj._b_param, 'new_b_param')
        self.assertEqual(obj._d_param, 'new_d_param')

    def test_init_check_no_positional(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self, positional):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_init_check_no_variadic(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self, *a):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_init_check_no_variadic_keywords(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self, **k):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_super_params_sends_params(self):
        @self.cls_decorator.im_func
        class _Fixed(self._F):
            __metaclass__ = self.cls_meta
            @coop.super_params(b_param='fixed_b_param')
            def __init__(self):
                pass
        obj = _Fixed()
        self.assertEqual(obj._b_param, 'fixed_b_param')

    def test_manual_init(self):
        outer_self = self
        @self.cls_decorator.im_func
        class _Manual(self._D):
            __metaclass__ = self.cls_meta
            @coop.manual_init
            def __init__(self, *a, **k):
                super(_Manual, self).__init__(*a, **k)
                outer_self._trace.append(_Manual.__init__)
        self._clear_trace()
        _Manual()
        self._check_trace_calls_with_mro(_Manual.__init__)

    def test_can_not_mix_non_cooperative_superclass(self):
        class NonCooperativeSuperClass(object):
            pass
        def make_class():
            @self.cls_decorator.im_func
            class _Bad(NonCooperativeSuperClass):
                __metaclass__ = self.cls_meta
        self.assertRaises(coop.CooperativeError, make_class)

    def test_can_mix_non_cooperative_subclass(self):
        class _Good(self._D):
            pass
        self._clear_trace()
        _Good()
        self._check_trace_calls_with_mro(self._D.__init__)

    def test_mro_call_order(self):
        for cls in (self._D, self._C, self._B, self._A):
            self._clear_trace()
            cls()
            self._check_trace_calls_with_mro(cls.__init__)

    def test_mro_does_not_decorate_undefined_init(self):
        self._clear_trace()
        self._F()
        self._check_trace_calls_with_mro(self._D.__init__)

    def _clear_trace(self):
        self._trace[:] = []

    def _check_trace_calls_with_mro(self, method):
        global _global_call_trace
        cls  = method.im_class
        name = method.__name__
        mro  = cls.__mro__[:-1] # discard object
        self.assertEqual(zip(mro[::-1], repeat(name)),
                         [(m.im_class, m.__name__) for m in self._trace])


class TestCoopMeta(TestCoop):

    cls_decorator = lambda x:x
    cls_meta      = coop.CooperativeMeta

    def test_meta_works_on_subclasses(self):
        outer_self = self
        class _NewClass(self._D):
            def __init__(self):
                outer_self._trace.append(_NewClass.__init__)
        self._clear_trace()
        _NewClass()
        self._check_trace_calls_with_mro(_NewClass.__init__)
