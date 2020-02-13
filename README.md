## PySExpr

A general-purpose package for gaining expression-first capability in Python
world, via transforming LISPs to the Python ASTs in applicative normal form,
enhanced by multiple techniques of register allocation optimizations.

```python
from rbnf.py_tools.unparse import Unparser
from py_sexpr import *
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
#
cfg = CFG(set(), (1, 1))
main.run(cfg)

node = ast.fix_missing_locations(astc.Module(cfg.build()))
# pprint(node)
Unparser(node)
```

```
=======PROG1========

def _pysexpr__main(this=None):
    _pysexpr__0 = 1
    _pysexpr__1 = 2
    _pysexpr__2 = _pysexpr__ge(_pysexpr__0, _pysexpr__1)
    if _pysexpr__2:
        _pysexpr__te()
    else:
        _pysexpr__fe()
    _pysexpr__3 = 1
    print(_pysexpr__3)
    _pysexpr__4 = 2
    _pysexpr__5 = _pysexpr__add1(_pysexpr__4)
    return _pysexpr__5
```