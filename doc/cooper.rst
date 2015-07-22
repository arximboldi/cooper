======
cooper
======

------------------------------------------------
Making super safe, a cooperative methods library
------------------------------------------------

.. contents::

Introduction
------------

Python's super_ keyword are a very useful tool to write cooperative
methods.  This is a method that cooperates with the other overrides in
the same hierarchy.  A good example of such a method is `__init__`, as
all the overrides must be called in class-hierarchy ascending order to
properly build an object.

Some interesting links before you proceed:

- `Python's super is nifty, but you can't use it <http://fuhm.net/super-harmful/>`__
- `Python's method resolution order <http://www.python.org/getit/releases/2.3/mro/>`__


The problem
~~~~~~~~~~~

Making cooperative methods in linear hierarchies is simple, but that
is not the case in the presence of multiple inheritance.  The problem
lies on the fact that the next override to be called is not known at
class definition time.  `James Knight rant
<http://fuhm.net/super-harmful/>`__ against super_ makes a very clear
exposition of the problem and proposes a methodology to use super_
consistently, if used at all.

We believe that super_ is very useful and many interesting and
expressive programming patterns arise when using horizontal
hierarchies extensively.  This library is attempt to make these safer
and usable in large projects.

.. _super: http://docs.python.org/library/functions.html#super


Basic usage
-----------

Our library does a lot magic inside.  When defining a class that we
want to have cooperative methods -- all your classes because
`__init__` should be cooperative indeed! -- you have to tell Python
this fact. There are two ways to do so.  In all the code bellow assume
that we have imported the library as in::

  from cooper import *

The class decorator method
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use a `class decorator
<http://www.python.org/dev/peps/pep-3129/>`__ to do so.  When using
this method, you should decorate every single cooperative class in
this way::

  class MyClass(object):
      ...
  MyClass = cooperative_class(MyClass)

Or in Python >= 2.7 with simplified syntax::

  @cooperative_class
  class MyClass(object):
      ...


The metaclass method
~~~~~~~~~~~~~~~~~~~~

You can also setup a cooperative class by overriding its
metaclass_, as in::

  class MyClass(object):
      __metaclass__ = CooperativeMeta
      ...

Or in Python >= 2.7 with simplified syntax::

  class MyClass(object, metaclass=CooperativeMeta):
      ...

Note that this automatically makes every child of `MyClass`
cooperative too. Also, we provide a `Cooperative` base class that
installs the metaclass. The easiest way to use the library is to just
inherit from it in your root classes::

  class MyClass(Cooperative):
      ...

.. _metaclass: http://docs.python.org/reference/datamodel.html#customizing-class-creation


Defining constructors
---------------------

In a cooperative class, just trying to override the constructor will
yield an error, as in::

  class MyClass(Cooperative):
      def __init__(self):
          pass

Yields::

  CooperativeError: Constructor should cooperate in cooperative class

You can fix the problem with the `cooperate` decorator. This will
automatically call the superclass constructor. For example::

  class Base(Cooperative):
      @cooperate
      def __init__(self):
          print "Base.__init__"

  class Deriv(Base):
      @cooperate
      def __init__(self):
          print "Deriv.__init__"

  Deriv()

When instantiating `Deriv` all constructors get called in increasing
order. The execution of this code outputs on the screens::

    Base.__init__
    Deriv.__init__


Parameter passing
~~~~~~~~~~~~~~~~~

When classes cooperate, you do not know the concrete of your upper
class. Inheriting from something means that they will be among your
super classes in that order, but there might be other classes that get
in between.  This means, that you do not know `the signature` of the
`__init__` method that is called next in the chain. To solve this, we
have to ensure two things:

1. That all cooperating overrides have the same positional
   arguments. Concretely, `__init__` should just have no positional
   arguments at all, and if you declare any an error will be raised.

2. We still want to be able to pass different parameters to the
   different classes above. What we do is a technique call `keyword
   picking`: we cherry pick any keyword parameters we need and pass
   the remaining ones to upper classes. The `cooperate` decorator
   takes care of that.

This example should clarify this::

  class Base(Cooperative):
      @cooperate
      def __init__(base_param=None)
          print "base_param = ", base_param

  class Deriv(Base):
      @cooperate
      def __init__(deriv_param=None)
          print "deriv_param = ", base_param

  Base(deriv_param = "Hello",
       base_param  = "world!")

This will output::

  base_param = Hello
  deriv_param = World!

As you see, all parameters should be passed with name. You can pass
parameters to upper classes constructors directly, each parameter
arrives the first class that picks it properly.  There are more ways
to this, but lets move now to see how to declare your own cooperative
methods.


Defining cooperative methods
----------------------------

While `__init__` and `__del__` are cooperative by default, other
methods and their overriding rules behave as normally. However it
might be interesting to have other methods behave like this.  For
example, in a computer game entities might have an `update` method
that updates its state on every new frame tick.

Every part of the entity should cooperate for the update, this, we can
enforce cooperative overrides for this method declaring it to be
cooperative in its first definition. Note that you can only cooperate
on a method that has been declared cooperative before in the
hierarchy, otherwise an error thrown.  Also, the same method should be
declared cooperative only once in the hierarchy, and an error is shown
otherwise.  This makes sure that you are overriding the method that
you want to override and that you made no mistakes when
multiple-inheriting in large code bases. For example::

    class Entity(Cooperative):
        @cooperative
        def update(self, timer):
            print "Entity.update"

    class Player(Entity):
        @cooperate
        def update(self, timer):
            print "Player.update"

    Player().update(0)

Will print::

    Entity.update
    Player.update

Note that the `update()` method above does indeed have parameters. The
library will ensure that the number of positional parameter matches,
and keyword parameter forwarding still works as with constructors.

Abstract methods
~~~~~~~~~~~~~~~~

It might happen that you are defining an abstract interface and you
want to enforce that someone overrides a method, in a cooperative
manner. The `abstract` decorator can be used to declare a cooperative
method to be abstract. Then, any attempt to instantiate a class with
non overriden abstract methods will throw a `TypeError` exception. For
example::

    class Abstract(Cooperative):
        @abstract
        def method(self):
            pass

    class Concrete(Abstract):
        @cooperate
        def method(self):
            print "Concrete.method"

    try:
        obj = Abstract()
    except TypeError:
        print "Abstract could not be instantiated".

    obj = Concrete()
    obj.method()

This will result in the following output::

   Abstract could not be instantiated
   Concrete.method

The library is compatible with the decorators defined in the `abc`
Python module. They work as normal thus you can define normal abstract
methods with them when you do not want cooperation::

    import abc

    class Abstract(Cooperative):
        @abc.abstractmethod
        def method(self):
            pass

    Abstract() # Error


Customizing cooperation
-----------------------

The `cooperate` decorator automatically calls the super-class method
definition, does keyword parameter forwarding and a lot useful magic,
but that might not be always what you want.  The library provides an
extensible family of cooperation decorators that you may use at will.


Post-order cooperation
~~~~~~~~~~~~~~~~~~~~~~

The `cooperate` class calls the super-class method definition *before*
the sub-class. This is what we want for constructors, state-updates
and most situations.

However, that is not always the case. For example, finalizers should
be called in the reverse order, i.e. subclasses firsts, to keep
super-class invariants while the sub-class part of the object is still
alive. The `post_cooperate` decorator does just that, as in the
example::

    class Entity(Cooperative):
        @cooperative
        def dispose(self):
            print "Entity.dispose"

    class ConcreteEntity(Entity):
        @post_cooperate
        def dispose(self):
            print "ConcreteEntity.dispose"

    ConcreteEntity().dispose()

Which yields::

    ConcreteEntity.dispose
    Entity.dispose


Fixing super-class parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes one might want to inject some fixed parameter values to some
superclass.  One can do that by using the `cooperate_with_params` or
`post_cooperate_with_params` decorators, as in::

    class TextWidget(Cooperative):
        @cooperate
        def __init__(self, color="black", background="white"):
            print "color = ", color
            print "background = ", background

    class ShadedTextWidget(TextWidget):
        @cooperate_with_params(color="gray")
        def __init__(self):
            pass

    ShadedTextWidget()

Which prints::

    color = gray
    background = white

Inner cooperation
~~~~~~~~~~~~~~~~~

Whenever we want to pass synthesised parameters upwards, or for some
other reason we want the super-classes to be invoked in the middle of
our method, we can use the `inner_cooperate` decorator.

In this case, the decorated method receives a `callable` as second
parameter that will execute the upper classes methods.  It
automatically will forward the received parameters and extra keywords
and you can pass extra keywords to it, as in example::

    class FunnyTextWidget(TextWidget):
        @inner_cooperate
        def __init__(self, next_method):
            import random
            random_color = random.choice(["green", "yellow", "red"])
            next_method (color = random_color)

**TODO**: Right now the `next_method` automatically forwards
positional parameters too. Should we change it such that it does not
so you can manipulate what is passed?

Manual cooperation
~~~~~~~~~~~~~~~~~~

While the previous decorators satisfy most needs, sometimes one must
call the superclass directly or not do it at all, for example, to
substitute a method with a mock in a test environment.

The `manual_cooperate` allows us to override a cooperative method with
an undecorated implementation. As whenever super_ is called manually,
this should be used with care.  Example::

    class MockEntity(Entity):
        @manual_cooperate
        def update(self, timer, **k):
            super(MockEntity, self).update(**k)
            self.updated_called = True

Defining new decorators
~~~~~~~~~~~~~~~~~~~~~~~

**TODO**: Explain how to define your own cooperation decorators by
inheriting from `CoopDecorator`.


Design with cooperative methods
-------------------------------

**TODO**: Write a section about how to design more horizontal
hierarchies and use `jpb.meta.mixin` to dynamically compose orthogonal
aspects as needed.


---------

*(c) Juan Pedro Bolívar Puente 2012*
