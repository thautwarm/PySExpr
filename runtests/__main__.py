from py_sexpr.terms import *
from py_sexpr.stack_vm.emit import module_code
import dis
main = define(
    "main", [],
    block(
        call(var("print"),
             ite(cmp(const(1), Compare.GT, const(2)), const(1), const(2))),
        const(1)))
print(eval(module_code(main))() == 1)

main = call(
    var("f"),
    block(call(var("print"), call(var("g"), var("x"))),
          assign("x", call(var("add"), var("x"), const((1, )))),
          call(var("print"), call(var("g"), var("x"))),
          assign("x", call(var("add"), var("x"), const((1, )))), var("x")))

add1 = module_code(
    define(None, ["x"],
           set_item(var("x"), 0, binop(get_item(var("x"), 0), BinOp.ADD, 1))))

x = [5]
f = lambda x: 'result {}'.format(x)
assert (eval(module_code(main),
             dict(f=f, add=lambda a, b: a + list(b), x=list(x),
                  g=eval(add1))) == f([x[0] + 2, 1, 1]))

main = block(
    define(
        "MyType", ["x", "y", "this"],
        block(set_item(var("this"), const("x"), var("x")),
              set_item(var("this"), const("y"), var("y")), var("this"))),
    assign_star("inst", new(var("MyType"), const(1), const(2))),
    isa(var("inst"), var("MyType")))

code = module_code(main)
assert eval(code) is True

xs = []

main = for_range("a", 1, 10, call(var("print"), var("a")))
exec(module_code(main), dict(print=xs.append))

assert xs == [1, 2, 3, 4, 5, 6, 7, 8, 9]

main = for_in("a", record(("a", 1), ("b", "bb")), call(var("print"), var("a")))
xs = []
exec(module_code(main), dict(print=xs.append))
assert set(xs) == {'a', 'b'}

main = call((define(None, ["x"], ret(mktuple(var("x"), var("x"))))), 1)
assert eval(module_code(main)) == (1, 1)

main = record()
assert eval(module_code(main)) == {}

RES = None
try:
    exec(module_code(throw(call(var("Exception"), "abc"))))
except Exception as e:
    RES = e.args[0]
assert RES == 'abc'

main = for_in("a", record(("a", const(1)), ("b", const("bb"))), block())
exec(module_code(main))

main = define("a", [], block(ret()))
assert eval(module_code(main))() is None

main = define("a", [], block(ret(5)))
assert eval(module_code(main))() == 5

main = define("a", [], metadata(2, 3, "a.txt", ret(const(2))))
assert eval(module_code(main))() == 2

main = define(None, ["x"],
              define(None, ["y"], binop(var("x"), BinOp.MULTIPLY, var("y"))))
code = module_code(main)
# dis.dis(code)
assert eval(code)(7)(3) == 21

main = define(
    None, ["x"],
    define(None, ["y"],
           define(None, ['z'], mktuple(var('x'), var('y'), var('z')))))
code = module_code(main)
# dis.dis(code)
assert eval(code)(7)(0)(2) == (7, 0, 2)

main = define(
    None, ["x"],
    block(
        assign("x'", var("x")),
        define(None, ["y"],
               define(None, ['z'], mktuple(var("x'"), var('y'), var('z'))))))
code = module_code(main)
# dis.dis(code)
assert eval(code)(7)(0)(2) == (7, 0, 2)

main = define(
    None, ["x"],
    block(
        assign("x", var("x")),
        define(None, ["y"],
               define(None, ['z'], mktuple(var("x"), var('y'), var('z'))))))
code = module_code(main)
# dis.dis(code)
assert eval(code)(7)(0)(2) == (7, 0, 2)

main = define(None, ["x"], block(define("f", [], var("x")), var("f")))
code = module_code(main)
# dis.dis(code)

assert eval(code)(1)() == 1

main = document(
    "the doc",
    define(
        None, ["x"],
        block(assign_star("y", binop(var("x"), BinOp.MODULO, 17)),
              assign_star("k", binop(var("y"), BinOp.MULTIPLY, 3)), var('k'))))
code = module_code(main)
# dis.dis(code)
f = eval(code)
assert f.__doc__ == 'the doc'
assert f(25) == 24

main = block(assign_star("x", record(a=1)),
             assign_star("y", lens(var("x"), record(a=2, b=3))), var("y"))
code = module_code(main)
# dis.dis(code)
assert eval(code) == dict(a=2, b=3)

main = block(assign_star("x", record(a=1)),
             assign_star("y", lens(var("x"), record(b=3))),
             var("y"))
code = module_code(main)
# dis.dis(code)
assert eval(code) == dict(a=1, b=3)

main = set_attr(var("o"), 'h', 1)
code = module_code(main)


# dis.dis(code)
class O:
    pass


exec(code, dict(o=O))
assert getattr(O, 'h') == 1

main = define(
    None, ["cond"],
    loop(
        cmp(var("cond"), Compare.GT, 0),
        block(assign("cond", binop(var("cond"), BinOp.SUBTRACT, 5)),
              var("cond"))))
code = module_code(main)

assert eval(code)(12) == -3

main = define(
    None, ["xyz"],
    mktuple(
        define('y', [], define('y-', [], var("xyz"))),
        define('z', [], define('z-', [], var("xyz"))),
    ))

code = module_code(main)
x, y = eval(code, {})(1)
assert x()() == y()() == 1

main = define(
    None, ["xyz"],
    define(
        'y', [],
        define(
            'yy', [],
            mktuple(
                define('y-', [], var("xyz")),
                define('z-', [], var("xyz")),
            ))))

code = module_code(main)
x, y = eval(code, {})(1)()()
assert x() == y() == 1

main = uop(UOp.INVERT, const(5))

code = module_code(main)
assert eval(code) == ~5


main = define(None, ["x"], var("x"), [1])

code = module_code(main)
f = eval(code)
assert f() == 1


main = block(define("f", [], var("f")), var("f"))
code = module_code(main)
f = eval(code)

assert f() == f