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
#
cfg = CFG(set(), (1, 1), default_return_tos=True)
main.run(cfg)

node = ast.fix_missing_locations(astc.Module(cfg.build()))
# pprint(node)
Unparser(node)
print('PROG2'.center(20, '='))
main = call(
    var("f"),
    block(
        call(extern("print"), call(var("g"), var("x"))),
        assign("x", call(var("add"), var("x"), const(1))),
        call(extern("print"), call(var("g"), var("x"))),
        assign("x", call(var("add"), var("x"), const(1))),
        call(var("g"), var("x")),
    ))

cfg = CFG(set(), (1, 1), default_return_tos=True)
main.run(cfg)

node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

main = block(
    define(
        "MyType", ["x", "y"],
        block(set_index(this, const("x"), var("x")),
              set_index(this, const("y"), var("y")))),
    assign("inst", new(var("MyType"), const(1), const(2))))

cfg = CFG(set(), (1, 1))
main.run(cfg)

node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)
