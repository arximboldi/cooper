# -*- coding: utf-8 -*-
#
#  File:       jpb_coop.py
#  Author:     Juan Pedro Bolívar Puente <raskolnikov@es.gnu.org>
#  Date:       Fri Jan 20 16:12:23 2012
#  Time-stamp: <2012-01-24 19:47:35 jbo>
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
        @coop.cooperate
        def __init__(self):
            trace.append(_A.__init__)
        @coop.cooperative
        def method(self, mparam):
            self._a_mparam = mparam
            trace.append(_A.method)
        @coop.cooperative
        def post_method(self, pmparam):
            self._a_pmparam = pmparam
            trace.append(_A.post_method)

    @decorator
    class _B(_A):
        __metaclass__ = metacls
        @coop.cooperate
        def __init__(self, b_param = 'b_param'):
            self._b_param = b_param
            trace.append(_B.__init__)
        @coop.cooperate
        def method(self, mparam, b_mparam='b_mparam'):
            self._b_mparam = b_mparam
            trace.append(_B.method)
        @coop.post_cooperate
        def post_method(self, pmparam, b_pmparam='b_mparam'):
            self._b_pmparam = b_pmparam
            trace.append(_B.post_method)


    @decorator
    class _C(_A):
        __metaclass__ = metacls
        @coop.cooperate
        def __init__(self):
            trace.append(_C.__init__)
        @coop.cooperate
        def method(self, mparam):
            self._c_mparam = mparam
            trace.append(_C.method)
        @coop.post_cooperate
        def post_method(self, pmparam):
            self._c_pmparam = pmparam
            trace.append(_C.post_method)

    @decorator
    class _D(_B, _C):
        __metaclass__ = metacls
        @coop.cooperate
        def __init__(self, d_param = 'd_param'):
            self._d_param = d_param
            trace.append(_D.__init__)
        @coop.cooperate
        def method(self, mparam, d_mparam='d_mparam'):
            self._d_mparam = d_mparam
            trace.append(_D.method)
        @coop.post_cooperate
        def post_method(self, pmparam, d_pmparam='d_mparam'):
            self._d_pmparam = d_pmparam
            trace.append(_D.post_method)

    @decorator
    class _F(_D, _A):
        __metaclass__ = metacls

    return _A, _B, _C, _D, _F


class TestCoop(unittest.TestCase):

    cls_decorator = coop.cooperative_class
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
                @coop.cooperate
                def __init__(self, positional):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_init_check_no_variadic(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                @coop.cooperate
                def __init__(self, *a):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_init_check_no_variadic_keywords(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                @coop.cooperate
                def __init__(self, **k):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_init_must_cooperate(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_init_must_override(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                @coop.cooperative
                def __init__(self):
                    pass
        self.assertRaises (coop.CooperativeError, make_cls)

    def test_super_params_sends_params(self):
        @self.cls_decorator.im_func
        class _Fixed(self._F):
            __metaclass__ = self.cls_meta
            @coop.cooperate_with_params(b_param='fixed_b_param')
            def __init__(self):
                pass
        obj = _Fixed()
        self.assertEqual(obj._b_param, 'fixed_b_param')

    def test_manual_init(self):
        outer_self = self
        @self.cls_decorator.im_func
        class _Manual(self._D):
            __metaclass__ = self.cls_meta
            @coop.manual_cooperate
            def __init__(self, *a, **k):
                super(_Manual, self).__init__(*a, **k)
                outer_self._trace.append(_Manual.__init__)
        self._clear_trace()
        _Manual()
        self._check_trace_calls_with_mro(_Manual.__init__)

    def test_can_mix_non_cooperative_superclass_single_inherit(self):
        class NonCooperativeSuperClass(object):
            pass
        @self.cls_decorator.im_func
        class _Good(NonCooperativeSuperClass):
            __metaclass__ = self.cls_meta
        self.assertTrue(isinstance(_Good(), _Good))

    def test_can_not_mix_non_cooperative_superclass_multi_inherit(self):
        class NonCooperativeSuperClass1(object):
            pass
        class NonCooperativeSuperClass2(object):
            pass
        def make_class():
            @self.cls_decorator.im_func
            class _Bad(NonCooperativeSuperClass1,
                       NonCooperativeSuperClass2):
                __metaclass__ = self.cls_meta
        self.assertRaises(coop.CooperativeError, make_class)

    def test_can_mix_non_cooperative_subclass(self):
        class _Good(self._D):
            pass
        self._clear_trace()
        _Good()
        self._check_trace_calls_with_mro(self._D.__init__)

    def test_abstract_method_forbids_instantiation(self):
        @self.cls_decorator.im_func
        class _ABC(self._D):
            __metaclass__ = self.cls_meta
            @coop.abstract
            def abstract_method(self):
                return 0
        self.assertRaises(TypeError, _ABC)

    def test_override_abstract_method_enables_instantiation(self):
        @self.cls_decorator.im_func
        class _ABC(self._D):
            __metaclass__ = self.cls_meta
            @coop.abstract
            def abstract_method(self):
                self._result = 1
        @self.cls_decorator.im_func
        class _Concrete(_ABC):
            __metaclass__ = self.cls_meta
            @coop.cooperate
            def abstract_method(self):
                return self._result
        self.assertEqual(_Concrete().abstract_method(), 1)

    def test_compatible_abstract_method_forbids_instantiation(self):
        import abc
        @self.cls_decorator.im_func
        class _ABC(self._D):
            __metaclass__ = self.cls_meta
            @abc.abstractmethod
            def abstract_method(self):
                return 0
        self.assertRaises(TypeError, _ABC)

    def test_compatible_override_abstract_method_enables_instantiation(self):
        import abc
        @self.cls_decorator.im_func
        class _ABC(self._D):
            __metaclass__ = self.cls_meta
            @abc.abstractmethod
            def abstract_method(self):
                return 0
        class _Concrete(_ABC):
            def abstract_method(self):
                return super(_Concrete, self).abstract_method()
        self.assertEqual(_Concrete().abstract_method(), 0)

    def test_conflict_raises_error(self):
        @self.cls_decorator.im_func
        class _A1(object):
            __metaclass__ = self.cls_meta
            @coop.cooperative
            def method(self):
                pass
        @self.cls_decorator.im_func
        class _A2(object):
            __metaclass__ = self.cls_meta
            @coop.cooperative
            def method(self):
                pass
        def make_class():
            @self.cls_decorator.im_func
            class _A12(_A1, _A2):
                __metaclass__ = self.cls_meta
                @coop.cooperate
                def method(self):
                    pass
        self.assertRaises(coop.CooperativeError, make_class)

    def test_mro_call_order(self):
        for cls in (self._D, self._C, self._B, self._A):
            obj = cls()
            self._clear_trace()
            obj.method(1)
            self._check_trace_calls_with_mro(cls.method)

    def test_post_mro_call_order(self):
        for cls in (self._D, self._C, self._B, self._A):
            obj = cls()
            self._clear_trace()
            obj.post_method(1)
            self._check_trace_calls_with_mro(cls.post_method, reverse=True)

    def test_mro_init_call_order(self):
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

    def _check_trace_calls_with_mro(self, method, reverse=False):
        cls  = method.im_class
        name = method.__name__
        mro  = cls.__mro__[:-1] # discard object
        self.assertEqual(zip(mro if reverse else mro[::-1], repeat(name)),
                         [(m.im_class, m.__name__) for m in self._trace])


class TestCoopMeta(TestCoop):

    cls_decorator = lambda x:x
    cls_meta      = coop.CooperativeMeta

    def test_meta_works_on_subclasses(self):
        outer_self = self
        class _NewClass(self._D):
            @coop.cooperate
            def __init__(self):
                outer_self._trace.append(_NewClass.__init__)
        self._clear_trace()
        _NewClass()
        self._check_trace_calls_with_mro(_NewClass.__init__)

class _TestBase(object):
    def __init__(self, param=None,*a, **k):
        super(_TestBase, self).__init__(*a, **k)
        assert param == 'param'
class _TestDeriv(_TestBase):
    def __init__(self, *a, **k):
        super(_TestDeriv, self).__init__(param='param',*a, **k)
class _CoopTestBase(coop.Cooperative):
    @coop.cooperate
    def __init__(self, param=None):
        assert param == 'param'
class _CoopTestDeriv(_CoopTestBase):
    @coop.cooperate_with_params(param='param')
    def __init__(self):
        pass

class _SimpleTestBase(object):
    def __init__(self, *a, **k):
        super(_SimpleTestBase, self).__init__(*a, **k)
class _SimpleTestDeriv(_SimpleTestBase):
    def __init__(self, *a, **k):
        super(_SimpleTestDeriv, self).__init__(*a, **k)
class _CoopSimpleTestBase(coop.Cooperative):
    @coop.cooperate
    def __init__(self):
        pass
class _CoopSimpleTestDeriv(_CoopSimpleTestBase):
    @coop.cooperate
    def __init__(self):
        pass

class _SuperSimpleTestBase(object): pass
class _SuperSimpleTestDeriv(_SuperSimpleTestBase): pass
class _SuperCoopSimpleTestBase(coop.Cooperative): pass
class _SuperCoopSimpleTestDeriv(_SuperCoopSimpleTestBase):  pass

class TestCoopPerformance(unittest.TestCase):

    def test_performance_overhead_override(self):
        import timeit
        t1 = min(timeit.repeat(_SimpleTestDeriv, number=1<<16))
        t2 = min(timeit.repeat(_CoopSimpleTestDeriv, number=1<<16))
        print
        print "Simple override -- Manual: ", t1, "  Coop: ", t2, "  Ratio: ", t2/t1

    def test_performance_overhead_no_override(self):
        import timeit
        t1 = min(timeit.repeat(_SuperSimpleTestDeriv, number=1<<16))
        t2 = min(timeit.repeat(_SuperCoopSimpleTestDeriv, number=1<<16))
        print
        print "No override -- Manual: ", t1, "  Coop: ", t2, "  Ratio: ", t2/t1

    def test_performance_overhead_with_params(self):
        import timeit
        t1 = min(timeit.repeat(_TestDeriv, number=1<<16))
        t2 = min(timeit.repeat(_CoopTestDeriv, number=1<<16))
        print
        print "Params -- Manual: ", t1, "  Coop: ", t2, "  Ratio: ", t2/t1

