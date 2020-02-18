# PySExpr of [Python-Compiler-Tools](https://github.com/python-compiler-tools)

[![PyPI version](https://img.shields.io/pypi/v/pysexpr.svg)](https://pypi.org/project/pysexpr)
[![Build Status](https://travis-ci.com/thautwarm/PySExpr.svg?branch=master)](https://travis-ci.com/thautwarm/PySExpr)
[![codecov](https://codecov.io/gh/thautwarm/PySExpr/branch/master/graph/badge.svg)](https://codecov.io/gh/thautwarm/PySExpr)
[![MIT License](https://img.shields.io/badge/license-MIT-Green.svg?style=flat)](https://github.com/thautwarm/EBNFParser/blob/boating-new/LICENSE)

A general-purpose package for gaining expression-first capability in Python
world. Currently implemented by taking advantage of Python bytecode, and available since Python 3.5, i.e.,
by using PySExpr as a cross-version compiler, you don't have to worry about the Python version. 

See [documentation](http://htmlpreview.github.io/?https://github.com/thautwarm/PySExpr/blob/gh-pages/docs/py_sexpr/index.html).

All constructors of PySExpr are documented [here](https://htmlpreview.github.io/?https://raw.githubusercontent.com/thautwarm/PySExpr/gh-pages/docs/py_sexpr/terms.html).

## Installation

```shell
pip install pysexpr
```

## What `PySExpr` is & is not?

PySExpr is a framework for better(cross-version, efficient, expressiveness) metaprogramming in Python.

PySExpr is not a programming language, but a code generation back end good to be targeted.

PySExpr is a killer tool when it comes to programmable programming in Python. Comparing to using Python ASTs,
we have perfect compatibility; in terms of generating Python code, PySExpr directly uses Python bytecode
and produces faster code, at the same time you can have **block expressions**, **assignment expressions**
or multiline-lambdas even in Python 3.5.

As this library is so useful, certainly there're many other scenarios for it to stand out. For example,
we can backport Python3.8/[PEP572](https://www.python.org/dev/peps/pep-0572/)'s assignment expressions to Python 3.5+, by composing this library with the mechanisms proposed by [future-strings](https://github.com/asottile/future-fstrings).


## Preview

```python
from py_sexpr.terms import *
from py_sexpr.stack_vm.emit import module_code

xs = []

main = block(
        assign_star("a", None),
        for_range("a", 1, 10, call(var("print"), var("a"))),
        )
exec(module_code(main), dict(print=xs.append))

assert xs == [1, 2, 3, 4, 5, 6, 7, 8, 9]
```
