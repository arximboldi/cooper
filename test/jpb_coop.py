# -*- coding: utf-8 -*-
#
#  File:       jpb_coop.py
#  Author:     Juan Pedro Bolívar Puente <raskolnikov@es.gnu.org>
#  Date:       Fri Jan 20 16:12:23 2012
#  Time-stamp: <2012-01-23 19:47:13 jbo>
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

    def test_constructor_parameter_passing(self):
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

    def test_constructor_check_no_positional(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self, positional):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_constructor_check_no_variadic(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self, *a):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_constructor_check_no_variadic_keywords(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self, **k):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_mro_call_order(self):
        for cls in (self._D, self._C, self._B, self._A):
            self._trace[:] = []
            cls()
            self._check_trace_calls_with_mro(cls.__init__)

    def test_mro_does_not_decorate_undefined_constructor(self):
        self._trace[:] = []
        self._F()
        self._check_trace_calls_with_mro(self._D.__init__)

    def _check_trace_calls_with_mro(self, method):
        global _global_call_trace
        cls  = method.im_class
        name = method.__name__
        mro  = cls.__mro__[:-1] # discard object
        self.assertEqual(list(mro[::-1]), [m.im_class for m in self._trace])
        for m in self._trace:
            m.__name__ == name


class TestCoopMeta(unittest.TestCase):

    cls_decorator = None
    cls_meta      = coop.CooperativeMeta
