"""One shot algebraic effect in Python!
"""
from types import GeneratorType
from typing import Callable


class AE(Exception):
    cont = None  # type: Callable


class Cont:
    def __init__(self, gen):
        self.gen = gen

    def __call__(self, i):
        return self.gen.send(i)


def ae0(f):
    """
    Marking a function that can throw algebraic effects.
    """
    def apply():
        try:
            gen = f()  # type: GeneratorType
        except StopIteration as e:
            return e.value
        eff = gen.send(None)
        eff.cont = consume(gen)
        raise eff

    return apply


def ae1(f):
    """
    Marking a function that can throw algebraic effects.
    """
    def apply(arg):
        try:
            gen = f(arg)  # type: GeneratorType
        except StopIteration as e:
            return e.value
        eff = gen.send(None)
        eff.cont = consume(gen)
        raise eff

    return apply


def ae2(f):
    """
    Marking a function that can throw algebraic effects.
    """
    def apply(arg1, arg2):
        try:
            gen = f(arg1, arg2)  # type: GeneratorType
        except StopIteration as e:
            return e.value
        eff = gen.send(None)
        eff.cont = consume(gen)
        raise eff

    return apply


def ae_n(f):
    def apply(*args, **kwargs):
        try:
            gen = f(*args, **kwargs)  # type: GeneratorType
        except StopIteration as e:
            return e.value
        eff = gen.send(None)
        eff.cont = consume(gen)
        raise eff

    return apply


def consume(f: GeneratorType):
    def apply(elt):
        try:
            eff = f.send(elt)  # type: GeneratorType
        except StopIteration as e:
            return e.value
        eff.cont = consume(f)
        raise eff

    return apply


if __name__ == '__main__':

    class A(AE):
        pass

    class B(AE):
        def __init__(self, value):
            self.value = value

    # noinspection PyTypeChecker
    @ae0
    def f():
        x = (yield A()) + 2
        return (yield B(x)) * 10

    try:
        print(f())
    except AE as eff:

        def handle(eff):
            z = 0
            while 1:
                try:
                    return eff.cont(z)
                except A as a:
                    eff = a
                except B as b:
                    eff = b
                    z = b.value

        print(handle(eff))
