"""This module provides interfaces to build S-expression.

**If you don't care about the implementation details, you only need to check this module.**
"""

import ast_compat as astc
from py_sexpr.stack_vm.instructions import BinOp, UOp
from bytecode.instr import Compare
from typing import List, Optional, Tuple

THIS_NAME = ".this"

Compare
"""enumeration of comparison operations"""

BinOp
"""enumeration of binary operations"""


def call(f, *args):
    return ('call', f, *args)


def assign(n: str, value):
    return 'assign', n, value


def define(func_name: Optional[str], args: List[str], body):
    args.append(THIS_NAME)
    return "func", args, body, func_name, [const(None)]


def const(constant):
    """
    a constant can be
    - a tuple made of constants
    - a float/int/str/complex/bool
    - None
    """
    return 'const', constant


def record(*args, **kv_pairs):
    return ('record', *args, *kv_pairs.items())


def lens(l, r):
    return 'lens', l, r


def throw(value):
    return 'throw', value


def isa(value, ty):
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


def cmp(l, op: Compare, r):
    return 'cmp', l, op, r


def binop(l, op: BinOp, r):
    return 'bin', l, op, r


def document(doc: str, term):
    return 'doc', doc, term


def new(ty, *args):
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
                      set_index(var("this"), const("y"), var("y")))),
            assign("inst", new(var("MyType"), const(1), const(2))))
    ```
    """
    return ('new', ty, *args)


def var(n: str):
    return "var", n


def mktuple(*values):
    """Make a tuple"""
    return ('tuple', *values)


def set_item(base, item, val):
    """Basically, `base[item] = value`, and the return value is `None`"""
    return "set_item", base, item, val


def get_item(base, item):
    """`base[item]`"""
    return "get_item", base, item


def set_attr(base, attr: str, val):
    """Basically, `base[item] = value`, and the return value is `None`"""
    return "set_attr", base, attr, val


def get_attr(base, attr: str):
    """`base[attr]`"""
    return "get_attr", base, attr


def block(*suite):
    """A block of s-expressions.

    If `suite` is empty, return value is `None`.

    Otherwise, the last expression in the block will be returned.
    """
    return ('block', *suite)


def for_range(n: str, low, high, body):
    """
    Basically it's
    ```python
    for n in range(low, high):
        body
    ```

    The return value is `None`.
    """
    return for_in(n, call(var("range"), low, high), body)


def for_in(n: str, obj, body):
    """
   Basically it's
   ```python
   for n in obj:
       body
   ```

   The return value is `None`.
   """
    return 'for_in', n, obj, body


def ite(cond, te, fe):
    """
    Basically it's
    ```python
    te if cond else fe
    ```

    Note that both `te` and `fe` can be block expression.
    """
    return 'ite', cond, te, fe


def loop(cond, body):
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


def ret(value=None):
    return 'ret', value


def metadata(line: int, column: int, filename: str, term):
    """Set metadata to s-expressions.
    """
    return 'line', line, ('filename', filename, term)


this = var(THIS_NAME)
