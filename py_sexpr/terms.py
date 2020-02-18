"""This module provides interfaces to build S-expression.

**If you don't care about the implementation details, you only need to check this module.**

------------------

`SExpr` is the type of our terms, and all Python leaf types also belong to it, such as
`int`, `float`, `bool`, `complex`, `None`, `str`.

To construct non-leaf `SExpr`s, you shall use SExpr constructors provided in this module.

For instance, to construct

- a variable, use `var("<varname>")`,

- a function call, use `call(f, arg1, arg2, ...)`, where `f`, `arg1`, ...,  are `SExpr`s,

- etc..

Note that, before assigning a variable, you should introduce it into current scope.

Following constructs can introduce variables:

- `define`: function name and arguments

- `assign_star`: LHS name

**Special attention that `assign` cannot introduce variables**.
"""
from py_sexpr.stack_vm.instructions import BinOp, UOp
from bytecode.instr import Compare
from typing import List, Optional, Union, Tuple
assert UOp
__all__ = [
    'Compare',
    'BinOp',
    'UOp',
    'call',
    'assign',
    'assign_star',
    'define',
    'const',
    'record',
    'lens',
    'throw',
    'isa',
    'cmp',
    'uop',
    'binop',
    'document',
    'metadata',
    'new',
    'var',
    'mktuple',
    'set_item',
    'set_attr',
    'get_item',
    'get_attr',
    'block',
    'for_range',
    'for_in',
    'ite',
    'loop',
    'ret',
 ]

if __debug__:
    """
    workaround pdoc
    """

    class TT(type):
        def __repr__(self):
            return 'SExpr'

    TT.__module__ = 'typing'
    SExpr = TT("SExpr", (), {})
    SExpr.__module__ = 'typing'
else:
    SExpr = Union[Tuple['SExpr', ...], int, float, complex, None, str, bool]
    SExpr = SExpr


def call(f: SExpr, *args: SExpr) -> SExpr:
    return ('call', f, *args)


def assign_star(n: str, value: SExpr) -> SExpr:
    """assign* can introduce new variables into current scope."""
    return 'assign_star', n, value


def assign(n: str, value: SExpr) -> SExpr:
    """NOTE: assign cannot introduce new variables."""
    return 'assign', n, value


def define(func_name: Optional[str], args: List[str], body: SExpr, defaults: Union[List[SExpr], Tuple[SExpr, ...]]=()):
    return "func", args, body, func_name, defaults


def const(constant: SExpr) -> SExpr:
    """
    This is necessary only if you needs tuple constants,
    otherwise `const(a)` is equal to `a`.

    A constant can be

    - a tuple made of constants

    - a "leaf" literal, i.e, one of `float`/`int`/`str`/`complex`/`bool`/`None`

    """
    return 'const', constant


def record(*args: SExpr, **kv_pairs: SExpr) -> SExpr:
    return ('record', *args, *kv_pairs.items())


def lens(l: SExpr, r: SExpr) -> SExpr:
    return 'lens', l, r


def throw(value: SExpr) -> SExpr:
    return 'throw', value


def isa(value: SExpr, ty: SExpr) -> SExpr:
    """Check if the left is instance of the right.

    Note that it doesn't use Python's isinstance protocol,
    even nor Python's object protocol.

    In fact, `isa(t1, t2)` means `t1['.t'] is t2`.

    We use only `dict`s to represent objects,
    and `dict['.t']` is the type.

    Inheritance feature is omitted, due to the lack of use cases.
    """
    lhs = ('call', ('get_attr', value, 'get'), const('.t'))
    return 'cmp', lhs, Compare.IS, ty


def cmp(l: SExpr, op: Compare, r: SExpr) -> SExpr:
    return 'cmp', l, op, r


def uop(op: UOp, term: SExpr) -> SExpr:
    return 'un', op, term


def binop(l: SExpr, op: BinOp, r: SExpr) -> SExpr:
    return 'bin', l, op, r


def document(doc: str, term: SExpr) -> SExpr:
    return 'doc', doc, term


def new(ty: SExpr, *args: SExpr) -> SExpr:
    """
    It's made for supporting javascript style new.

    e.g., for following JS code
    ```javascript
        function MyType(x, y) {
            this.x = x
            this.y = y
        }
        inst = new MyType(1, 2)
    ```
    you can use this PySExpr expression to build
    ```python
        block(
            define(
                "MyType", ["x", "y"],
                block(set_index(var("this"), const("x"), var("x")),
                      set_index(var("this"), const("y"), var("y")),
                      this)),
            assign("inst", new(var("MyType"), const(1), const(2))))
    ```
    """
    return ('new', ty, *args)


def var(n: str) -> SExpr:
    return "var", n


def mktuple(*values: SExpr) -> SExpr:
    """Make a tuple"""
    return ('tuple', *values)


def set_item(base: SExpr, item: SExpr, val: SExpr) -> SExpr:
    """Basically, `base[item] = value`, and the return value is `None`"""
    return "set_item", base, item, val


def get_item(base: SExpr, item: SExpr) -> SExpr:
    """`base[item]`"""
    return "get_item", base, item


def set_attr(base: SExpr, attr: str, val: SExpr) -> SExpr:
    """Basically, `base[item] = value`, and the return value is `None`"""
    return "set_attr", base, attr, val


def get_attr(base: SExpr, attr: str) -> SExpr:
    """`base[attr]`"""
    return "get_attr", base, attr


def block(*suite: SExpr) -> SExpr:
    """A block of s-expressions.

    If `suite` is empty, return value is `None`.

    Otherwise, the last expression in the block will be returned.
    """
    return ('block', *suite)


def for_range(n: str, low: SExpr, high: SExpr, body: SExpr) -> SExpr:
    """
    Basically it's
    ```python
    for n in range(low, high):
        body
    ```

    The return value is `None`.
    """
    return for_in(n, call(var("range"), low, high), body)


def for_in(n: str, obj: SExpr, body: SExpr) -> SExpr:
    """
   Basically it's
   ```python
   for n in obj:
       body
   ```

   The return value is `None`.
   """
    return 'for_in', n, obj, body


def ite(cond: SExpr, te: SExpr, fe: SExpr) -> SExpr:
    """
    Basically it's
    ```python
    te if cond else fe
    ```

    Note that both `te` and `fe` can be block expression.
    """
    return 'ite', cond, te, fe


def loop(cond: SExpr, body: SExpr) -> SExpr:
    """
    Basically it's
    ```python
    while cond:
        body
    ```

    However, the return will be `body` in the last iteration.

    If no iteration performed, `None` is returned.
    """
    return 'loop', cond, body


def ret(value: SExpr = None) -> SExpr:
    return 'ret', value


def metadata(line: int, column: int, filename: str, term: SExpr) -> SExpr:
    """Set metadata to s-expressions.
    """
    return 'line', line, ('filename', filename, term)
