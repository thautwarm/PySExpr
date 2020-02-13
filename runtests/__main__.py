import ast
import astor
import sys
from py_sexpr.terms import *


def Unparser(x):
    if sys.version_info >= (3, 8):
        return
    print(astor.to_source(x))


print()
print('PROG1'.center(30, '='))
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

print()
print('PROG2'.center(30, '='))
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

print()
print('PROG3'.center(30, '='))
main = block(
    define(
        "MyType", ["x", "y"],
        block(set_index(this, const("x"), var("x")),
              set_index(this, const("y"), var("y")))),
    assign("inst", new(var("MyType"), const(1), const(2))),
    call(extern("print"), isa(var("inst"), var("MyType"))))
cfg = CFG(set(), (1, 1))
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG4'.center(30, '='))
main = for_range("a", const(1), const(10), call(extern("print"), var("a")))
cfg = CFG(set(), (1, 1))
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG5'.center(30, '='))
main = for_in("a", mkdict([("a", const(1)), ("b", const("bb"))]),
              call(extern("print"), var("a")))

cfg = CFG(set(), (1, 1))
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG6'.center(30, '='))
main = call((define(None, ["x"], ret(mktuple(var("x"), var("x"))))), var("1"))
cfg = CFG(set(), (1, 1), default_return_tos=True)
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG7'.center(30, '='))
main = call(extern("print"), mkdict([]))
cfg = CFG(set(), (1, 1), default_return_tos=True)
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG8'.center(30, '='))
main = throw(mkdict([]))
cfg = CFG(set(), (1, 1), default_return_tos=True)
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG9'.center(30, '='))
main = for_in("a", mkdict([("a", const(1)), ("b", const("bb"))]), block())
cfg = CFG(set(), (1, 1))
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG10'.center(30, '='))
main = define("a", [], block(ret()))
cfg = CFG(set(), (1, 1))
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)

print()
print('PROG11'.center(30, '='))
main = define("a", [], loc(2, 3, ret(const(2))))
cfg = CFG(set(), (1, 1))
main.run(cfg)
node = ast.fix_missing_locations(astc.Module(cfg.build()))
Unparser(node)
