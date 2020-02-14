"""Basic constructs of a tagless final style ANF transformation.
"""
import ast_compat as astc
import ast
from contextlib import contextmanager
from typing import Dict, Tuple, Iterable, List, Optional
from py_sexpr.facility import *
from py_sexpr.linear_scan import LiveInterval, linear_scan

invoke = lambda arg: lambda f: f(arg)


def call(f, *args):
    def run(module):
        return module.call(f(module), *map(invoke(module), args))

    return run


def var(s: str):
    def run(module):
        return module.var(s)

    return run


def fun(name: Optional[str], args: List[str], body):
    def run(module):
        return module.fun(name, args, body(module))

    return run
