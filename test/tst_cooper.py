# -*- coding: utf-8 -*-
#
#  File:       cooper.py
#  Author:     Juan Pedro Bolívar Puente <raskolnikov@es.gnu.org>
#  Date:       Fri Jan 20 16:12:23 2012
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
Tests for cooper.
"""

import cooper
from itertools import repeat

import unittest


def make_test_hierarchy(trace, decorator=lambda x:x, metacls=type):

    @decorator
    class _A(object):
        __metaclass__ = metacls
        @cooper.cooperate
        def __init__(self):
            trace.append(_A.__init__)
        @cooper.cooperative
        def method(self, mparam):
            self._a_mparam = mparam
            trace.append(_A.method)
        @cooper.cooperative
        def post_method(self, pmparam):
            self._a_pmparam = pmparam
            trace.append(_A.post_method)

    @decorator
    class _B(_A):
        __metaclass__ = metacls
        @cooper.cooperate
        def __init__(self, b_param = 'b_param'):
            self._b_param = b_param
            trace.append(_B.__init__)
        @cooper.cooperate
        def method(self, mparam, b_mparam='b_mparam'):
            self._b_mparam = b_mparam
            trace.append(_B.method)
        @cooper.post_cooperate
        def post_method(self, pmparam, b_pmparam='b_mparam'):
            self._b_pmparam = b_pmparam
            trace.append(_B.post_method)


    @decorator
    class _C(_A):
        __metaclass__ = metacls
        @cooper.cooperate
        def __init__(self):
            trace.append(_C.__init__)
        @cooper.cooperate
        def method(self, mparam):
            self._c_mparam = mparam
            trace.append(_C.method)
        @cooper.post_cooperate
        def post_method(self, pmparam):
            self._c_pmparam = pmparam
            trace.append(_C.post_method)

    @decorator
    class _D(_B, _C):
        __metaclass__ = metacls
        @cooper.cooperate
        def __init__(self, d_param = 'd_param'):
            self._d_param = d_param
            trace.append(_D.__init__)
        @cooper.cooperate
        def method(self, mparam, d_mparam='d_mparam'):
            self._d_mparam = d_mparam
            trace.append(_D.method)
        @cooper.post_cooperate
        def post_method(self, pmparam, d_pmparam='d_mparam'):
            self._d_pmparam = d_pmparam
            trace.append(_D.post_method)

    @decorator
    class _F(_D, _A):
        __metaclass__ = metacls

    return _A, _B, _C, _D, _F


class TestCoop(unittest.TestCase):

    cls_decorator = cooper.cooperative_class
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
                @cooper.cooperate
                def __init__(self, positional):
                    pass
        self.assertRaises (cooper.CooperativeError, make_cls)

    def test_init_check_no_variadic(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                @cooper.cooperate
                def __init__(self, *a):
                    pass
        self.assertRaises (cooper.CooperativeError, make_cls)

    def test_init_check_no_variadic_keywords(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                @cooper.cooperate
                def __init__(self, **k):
                    pass
        self.assertRaises (cooper.CooperativeError, make_cls)

    def test_init_must_cooperate(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                def __init__(self):
                    pass
        self.assertRaises (cooper.CooperativeError, make_cls)

    def test_init_must_override(self):
        def make_cls():
            @self.cls_decorator.im_func
            class _Bad(object):
                __metaclass__ = self.cls_meta
                @cooper.cooperative
                def __init__(self):
                    pass
        self.assertRaises (cooper.CooperativeError, make_cls)

    def test_super_params_sends_params(self):
        @self.cls_decorator.im_func
        class _Fixed(self._F):
            __metaclass__ = self.cls_meta
            @cooper.cooperate_with_params(b_param='fixed_b_param')
            def __init__(self):
                pass
        obj = _Fixed()
        self.assertEqual(obj._b_param, 'fixed_b_param')

    def test_manual_init(self):
        outer_self = self
        @self.cls_decorator.im_func
        class _Manual(self._D):
            __metaclass__ = self.cls_meta
            @cooper.manual_cooperate
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
        self.assertRaises(cooper.CooperativeError, make_class)

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
            @cooper.abstract
            def abstract_method(self):
                return 0
        self.assertRaises(TypeError, _ABC)

    def test_override_abstract_method_enables_instantiation(self):
        @self.cls_decorator.im_func
        class _ABC(self._D):
            __metaclass__ = self.cls_meta
            @cooper.abstract
            def abstract_method(self):
                self._result = 1
        @self.cls_decorator.im_func
        class _Concrete(_ABC):
            __metaclass__ = self.cls_meta
            @cooper.cooperate
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
            @cooper.cooperative
            def method(self):
                pass
        @self.cls_decorator.im_func
        class _A2(object):
            __metaclass__ = self.cls_meta
            @cooper.cooperative
            def method(self):
                pass
        def make_class():
            @self.cls_decorator.im_func
            class _A12(_A1, _A2):
                __metaclass__ = self.cls_meta
                @cooper.cooperate
                def method(self):
                    pass
        self.assertRaises(cooper.CooperativeError, make_class)

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

    def test_inner_cooperate(self):
        outer_self = self
        @self.cls_decorator.im_func
        class _Cls(self._D):
            __metaclass__ = self.cls_meta
            @cooper.inner_cooperate
            def method(self, next_method, param):
                next_method(b_mparam='new_b_mparam')
                outer_self._trace.append(_Cls.method)
        obj = _Cls()
        self._clear_trace()
        obj.method(1)
        self._check_trace_calls_with_mro(_Cls.method)
        self.assertEqual(obj._b_mparam, 'new_b_mparam')

    def test_inner_error_call_too_much(self):
        @self.cls_decorator.im_func
        class _Cls(self._D):
            __metaclass__ = self.cls_meta
            @cooper.inner_cooperate
            def method(self, next_method, param):
                next_method()
                next_method()
        obj = _Cls()
        self.assertRaises(cooper.CooperativeError, obj.method, 1)

    def test_inner_error_not_call(self):
        @self.cls_decorator.im_func
        class _Cls(self._D):
            __metaclass__ = self.cls_meta
            @cooper.inner_cooperate
            def method(self, next_method, param):
                pass
        obj = _Cls()
        self.assertRaises(cooper.CooperativeError, obj.method, 1)

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
    cls_meta      = cooper.CooperativeMeta

    def test_meta_works_on_subclasses(self):
        outer_self = self
        class _NewClass(self._D):
            @cooper.cooperate
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
class _CoopTestBase(cooper.Cooperative):
    @cooper.cooperate
    def __init__(self, param=None):
        assert param == 'param'
class _CoopTestDeriv(_CoopTestBase):
    @cooper.cooperate_with_params(param='param')
    def __init__(self):
        pass

class _SimpleTestBase(object):
    def __init__(self, *a, **k):
        super(_SimpleTestBase, self).__init__(*a, **k)
class _SimpleTestDeriv(_SimpleTestBase):
    def __init__(self, *a, **k):
        super(_SimpleTestDeriv, self).__init__(*a, **k)
class _CoopSimpleTestBase(cooper.Cooperative):
    @cooper.cooperate
    def __init__(self):
        pass
class _CoopSimpleTestDeriv(_CoopSimpleTestBase):
    @cooper.cooperate
    def __init__(self):
        pass

class _SuperSimpleTestBase(object): pass
class _SuperSimpleTestDeriv(_SuperSimpleTestBase): pass
class _SuperCoopSimpleTestBase(cooper.Cooperative): pass
class _SuperCoopSimpleTestDeriv(_SuperCoopSimpleTestBase):  pass

class TestCoopPerformance(unittest.TestCase):

    test_number = 1<<8

    def test_performance_overhead_override(self):
        import timeit
        t1 = min(timeit.repeat(_SimpleTestDeriv, number=self.test_number))
        t2 = min(timeit.repeat(_CoopSimpleTestDeriv, number=self.test_number))
        print
        print "Simple override -- "
        print "   Manual: ", t1
        print "   Coop:   ", t2
        print "   Ratio:  ", t2/t1

    def test_performance_overhead_no_override(self):
        import timeit
        t1 = min(timeit.repeat(_SuperSimpleTestDeriv, number=self.test_number))
        t2 = min(timeit.repeat(_SuperCoopSimpleTestDeriv, number=self.test_number))
        print
        print "No override -- "
        print "   Manual: ", t1
        print "   Coop:   ", t2
        print "   Ratio:  ", t2/t1

    def test_performance_overhead_with_params(self):
        import timeit
        t1 = min(timeit.repeat(_TestDeriv, number=self.test_number))
        t2 = min(timeit.repeat(_CoopTestDeriv, number=self.test_number))
        print
        print "Params -- "
        print "   Manual: ", t1
        print "   Coop:   ", t2
        print "   Ratio:  ", t2/t1
