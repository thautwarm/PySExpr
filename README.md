# PySExpr of [Python-Compiler-Tools](https://github.com/python-compiler-tools)

[![PyPI version](https://img.shields.io/pypi/v/pysexpr.svg)](https://pypi.org/project/pysexpr)
[![Build Status](https://travis-ci.com/thautwarm/PySExpr.svg?branch=master)](https://travis-ci.com/thautwarm/PySExpr)
[![codecov](https://codecov.io/gh/thautwarm/PySExpr/branch/master/graph/badge.svg)](https://codecov.io/gh/thautwarm/PySExpr)
[![MIT License](https://img.shields.io/badge/license-MIT-Green.svg?style=flat)](https://github.com/thautwarm/EBNFParser/blob/boating-new/LICENSE)

A general-purpose package for gaining expression-first capability in Python
world. Current by taking advantage of Python bytecode. 

See [documentation](http://htmlpreview.github.io/?https://github.com/thautwarm/PySExpr/blob/gh-pages/docs/py_sexpr/index.html).

All constructors of PySExpr are documented [here](https://htmlpreview.github.io/?https://raw.githubusercontent.com/thautwarm/PySExpr/gh-pages/docs/py_sexpr/terms.html).

## Preview

```python
from py_sexpr.terms import *
from py_sexpr.stack_vm.emit import module_code

xs = []

main = for_range("a", 1, 10, call(var("print"), var("a")))
exec(module_code(main), dict(print=xs.append))

assert xs == [1, 2, 3, 4, 5, 6, 7, 8, 9]
```
