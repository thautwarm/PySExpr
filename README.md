# PySExpr

A general-purpose package for gaining expression-first capability in Python
world, via transforming LISPs to the Python ASTs in applicative normal form,
enhanced by multiple techniques of register allocation optimizations.

See [Documentation](http://htmlpreview.github.io/?https://github.com/thautwarm/PySExpr/blob/gh-pages/docs/py_sexpr/index.html).

All constructors of PySExpr are documented [here](https://htmlpreview.github.io/?https://raw.githubusercontent.com/thautwarm/PySExpr/gh-pages/docs/py_sexpr/terms.html).

## Preview

```python
import ast
from rbnf.py_tools.unparse import Unparser
from py_sexpr.terms import *
print('PROG1'.center(20, '='))
main = define(
    "main", [],
    block(
        ite(
            call(var("ge"), const(1), const(2)),
            call(var("te")),
            call(var("fe")),
        ),
        call(extern("print"), const(1)),
        call(var("add1"), const(2)),
    ))

cfg = CFG(set(), (1, 1), default_return_tos=True)
main.run(cfg)

node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)
```
=>
```python
def _pysexpr_main(this=None):
    _pysexpropt_1 = 1
    _pysexpropt_2 = 2
    _pysexpropt_3 = _pysexpr_ge(_pysexpropt_1, _pysexpropt_2)
    if _pysexpropt_3:
        _pysexpr_te()
    else:
        _pysexpr_fe()
    _pysexpropt_1 = 1
    print(_pysexpropt_1)
    _pysexpropt_3 = 2
    _pysexpropt_2 = _pysexpr_add1(_pysexpropt_3)
    return _pysexpropt_2
```