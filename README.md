cooper
======

> Making super safe, a cooperative methods library

Python's `super` is a very useful tool to write cooperative methods.
A *cooperative method* is one such that cooperates with the other
overrides in the same hierarchy.  A good example is `__init__`, as all
the overrides must be called in class-hierarchy ascending order to
properly build an object.

![Gary Cooper](doc/gary-cooper.jpg)

Installation
------------

```
$ pip install cooper
```

The problem
-----------

Making cooperative methods in linear hierarchies is simple, but that
is not the case in the presence of multiple inheritance.  The problem
lies on the fact that the next override to be called is not known at
class definition time.
[James Knight rant](http://fuhm.net/super-harmful) against `super` makes
a very clear exposition of the problem and proposes a methodology to
use `super` consistently, if used at all.

We believe that `super` is very useful and many interesting and
expressive programming patterns arise when using horizontal
hierarchies extensively.  This library is attempt to make these safer
and usable in large projects.

Examples
--------

```
from cooper import *
```

### Cooperative constructors

```python
  class Base(Cooperative):
      @cooperate
      def __init__(self):
          print "Base.__init__"

  class Deriv(Base):
      @cooperate
      def __init__(self):
          print "Deriv.__init__"

   Deriv()
```

> **Output**
> ```
>     Base.__init__
>     Deriv.__init__
> ```

### Automatic argument forwarding

```python
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
```

> **Output:**
> ```
>     base_param = Hello
>     deriv_param = World!
> ```

### Other methods

```python
    class Entity(Cooperative):
        @cooperative
        def update(self, timer):
            print "Entity.update"

    class Player(Entity):
        @cooperate
        def update(self, timer):
            print "Player.update"

    Player().update(0)
```

> **Output:**
> ```
>     Entity.update
>     Player.update
> ```

### Abstract methods

```python
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
```

> **Output:**
> ```
>    Abstract could not be instantiated
>    Concrete.method
> ```

### Compatibility with standard abstract methods

```python
    import abc

    class Abstract(Cooperative):
        @abc.abstractmethod
        def method(self):
            pass

    Abstract() # Error
```

### Post-cooperation

```python
    class Entity(Cooperative):
        @cooperative
        def dispose(self):
            print "Entity.dispose"

    class ConcreteEntity(Entity):
        @post_cooperate
        def dispose(self):
            print "ConcreteEntity.dispose"

    ConcreteEntity().dispose()
```

> **Output:**
> ```
>     ConcreteEntity.dispose
>     Entity.dispose
> ```

### Fix arguments to superclass

```python
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
```

> **Output:**
> ```
>     color = gray
>     background = white
> ```

### Inner cooperation

```python
    import random

    class FunnyTextWidget(TextWidget):
        @inner_cooperate
        def __init__(self, next_method):
            random_color = random.choice(["green", "yellow", "red"])
            next_method (color = random_color)
```

### Manual cooperation

```python
    class MockEntity(Entity):
        @manual_cooperate
        def update(self, timer, **k):
            super(MockEntity, self).update(**k)
            self.updated_called = True
```

References
----------

- [Python's super is nifty, but you can't use it](http://fuhm.net/super-harmful)
- [Python's method resolution order](http://www.python.org/getit/releases/2.3/mro/)

License
-------

> Copyright (c) 2012, 2015 Juan Pedro Bolivar Puente <raskolnikov@gnu.org>
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in
> all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
> THE SOFTWARE.
