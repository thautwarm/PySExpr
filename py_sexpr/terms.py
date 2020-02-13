"""This module provides interfaces to build S-expression.

**If you don't care about the implementation details, you only need to check this module.**
"""

import ast_compat as astc
from typing import List, Optional, Tuple
from py_sexpr.base import Term, CFG, use_many
from py_sexpr.facility import *


def call(f_: Term, *args_: Term):
    @Term
    def run(self: CFG):
        f = f_.run(self)
        args = (arg.run(self) for arg in args_)
        with f.use(self) as f, use_many(args, self) as args:
            ast_call = astc.Call(func=f, args=list(args))
            return self.push(ast_call, can_elim=False)

    return run


def assign(n: str, value_: Term):
    @Term
    def run(self: CFG):
        value = value_.run(self)
        with value.use(self) as value:
            self.add_stmt(astc.Assign([name_of_id(n, LHS)], value))
            return self.push(NONE, can_elim=True)

    return run


def define(func_name_: Optional[str], args_: List[str], body_: Term):
    @Term
    def run(self: CFG):
        func_name = func_name_
        args = args_
        body = body_

        if func_name is None:
            func_name = self.alloc()
        else:
            func_name = prefixed(func_name)

        sub = self.sub_cfg()

        body = body.run(sub)
        # return TOP by default?
        # if so:
        if sub.ret_tos:
            with body.use(sub) as body:
                sub.add_stmt(astc.Return(body))

        args = [astc.arg(arg=prefixed(n)) for n in args]
        args.append(astc.arg(arg='this'))
        args = astc.arguments(args=args, defaults=[NONE])

        body = sub.build()
        self.add_stmt(astc.FunctionDef(name=func_name, args=args, body=body))

        return self.push(name_of_id(func_name, RHS), can_elim=True)

    return run


def const(constant):
    """
    a constant can be
    - a tuple made of constants
    - a float/int/str/complex/bool
    - None
    """
    @Term
    def run(self: CFG):
        return self.push(astc.Constant(constant), can_elim=True)

    return run


def mkdict(kv_pairs: List[Tuple[str, Term]]):
    @Term
    def run(self: CFG):

        if not kv_pairs:
            keys, values = (), ()
        else:
            keys, values = zip(*kv_pairs)
            values = (v.run(self) for v in values)
        with use_many(values, self) as values:
            ast_dict = astc.Dict(keys=[astc.Constant(k) for k in keys],
                                 values=values)
            return self.push(ast_dict, can_elim=True)

    return run


def throw(value_: Term):
    @Term
    def run(self: CFG):
        with value_.run(self).use(self) as value:
            self.add_stmt(astc.Raise(exc=value))
            return self.push(NONE, can_elim=True)

    return run


def isa(value_: Term, ty_: Term):
    """Check if the left is instance of the right.

    Note that it doesn't use Python's isinstance protocol,
    even nor Python's object protocol.

    In fact, `isa(t1, t2)` means `t1['.t'] is t2`.

    We use only `dict`s to represent objects,
    and `dict['.t']` is the type.

    Inheritance feature is omitted, due to the lack of use cases.
    """
    @Term
    def run(self: CFG):
        with value_.run(self).use(self) as value, ty_.run(self).use(
                self) as ty:
            lookup = astc.Attribute(value=value, attr='get', ctx=RHS)
            cmp = same_as(astc.Call(func=lookup, args=[astc.Constant('.t')]),
                          ty)

            return self.push(cmp, can_elim=True)

    return run


def new(ty_: Term, *args_: Term):
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
                block(set_index(this, const("x"), var("x")),
                      set_index(this, const("y"), var("y")))),
            assign("inst", new(var("MyType"), const(1), const(2))))
    ```
    """
    @Term
    def run(self: CFG):
        args = (each.run(self) for each in args_)
        with ty_.run(self).use(self) as ty, use_many(args, self) as args:
            inst = astc.Dict(keys=[astc.Constant('.t')], values=[ty])
            with self.push(inst, can_elim=True).use(self) as inst:
                args.append(inst)
                self.add_stmt(astc.Expr(astc.Call(func=ty, args=args)))
                return self.push(inst, can_elim=True)

    return run


def var(n: str):
    @Term
    def run(self: CFG):
        return self.push(name_of_id(prefixed(n), RHS), can_elim=True)

    return run


def _this(self: CFG):
    """indicating the instance itself, like `self` in Python or `this` in C/CPP
    """
    return self.push(name_of_id("this", RHS), can_elim=True)


this = _this
"""indicating the instance itself, like `self` in Python or `this` in C/CPP"""


def extern(n: str):
    """
    Use this to disable mangling to get Python's builtin objects.
    e.g, `extern("print")` is Python's `print`.
    """
    @Term
    def run(self: CFG):
        return self.push(name_of_id(n, RHS), can_elim=True)

    return run


def mktuple(*values_: Term):
    """Make a tuple"""
    @Term
    def run(self: CFG):
        values = (each.run(self) for each in values_)
        with use_many(values, self) as values:
            ast_tuple = astc.Tuple(elts=values, ctx=RHS)
            return self.push(ast_tuple, can_elim=True)

    return run


def set_index(base_: Term, item_: Term, value_: Term):
    """Basically, `base_[item_] = value_`, and the return value is `None`"""
    @Term
    def run(self: CFG):
        base, item, value = base_.run(self), item_.run(self), value_.run(self)
        with base.use(self) as base, item.use(self) as item, value.use(
                self) as value:
            lhs = astc.Subscript(value=base,
                                 slice=astc.Index(value=item),
                                 ctx=LHS)
            self.add_stmt(astc.Assign(targets=[lhs], value=value))
            return self.push(NONE, can_elim=True)

    return run


def block(*suite: Term):
    """A block of s-expressions.

    If `suite` is empty, return value is `None`.

    Otherwise, the last expression in the block will be returned.
    """
    @Term
    def run(self: CFG):
        if not suite:
            return self.push(NONE, can_elim=True)
        *init, end = (each.run(self) for each in suite)
        with end.use(self) as end:
            return self.push(end, can_elim=True)

    return run


def for_range(n_: str, low_: Term, high_: Term, body: Term):
    """
    Basically it's
    ```python
    for n_ in range(low_, high_):
        body
    ```

    The return value is `None`.
    """
    @Term
    def run(self: CFG):
        n = prefixed(n_)
        sub = self.sub_cfg()
        low = low_.run(self)
        high = high_.run(self)
        with low.use(self) as low, high.use(self) as high:
            body.run(sub)
            ast_for = astc.For(target=name_of_id(n, LHS),
                               iter=astc.Call(name_of_id('range', RHS),
                                              args=[low, high]),
                               body=sub.build())
            self.add_stmt(ast_for)
            return self.push(NONE, can_elim=True)

    return run


def for_in(n_: str, obj_: Term, body_: Term):
    """
   Basically it's
   ```python
   for n_ in obj_:
       body_
   ```

   The return value is `None`.
   """
    @Term
    def run(self: CFG):
        n = prefixed(n_)
        with obj_.run(self).use(self) as obj:
            sub = self.sub_cfg()
            body_.run(sub)
            ast_for = astc.For(target=name_of_id(n, LHS),
                               iter=obj,
                               body=sub.build())
            self.add_stmt(ast_for)
            return self.push(NONE, can_elim=True)

    return run


def ite(cond_: Term, te: Term, fe: Term):
    """
    Basically it's
    ```python
    if cond_:
        te
    else:
        fe
    ```

    Take care that the return value is `None`.
    """
    @Term
    def run(self: CFG):
        with cond_.run(self).use(self) as cond:
            sub1 = self.sub_cfg()
            sub2 = self.sub_cfg()

            te.run(sub1)
            fe.run(sub2)

            ast_if = astc.If(test=cond, body=sub1.build(), orelse=sub2.build())
            self.add_stmt(ast_if)
            return self.push(NONE, can_elim=True)

    return run


def ret(value_: Term = None):
    @Term
    def run(self: CFG):
        if value_ is None:
            self.add_stmt(astc.Return())
        else:
            with value_.run(self).use(self) as value:
                ast_ret = astc.Return(value)
                self.add_stmt(ast_ret)
        return self.push(NONE, can_elim=True)

    return run


def loc(line: int, column: int, term: Term):
    """Set location to s-expressions.
    """
    @Term
    def run(self: CFG):
        self.loc = (line, column)
        return term.run(self)

    return run
