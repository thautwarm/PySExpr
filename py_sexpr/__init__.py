import ast_compat as astc
import ast
from contextlib import contextmanager
from sortedcontainers import SortedDict, SortedKeyList
from typing import Dict, List, Tuple, Optional, Iterable
from enum import Enum


class Term:
    def __init__(self, higher_rank_func):
        self.f = higher_rank_func

    def run(self, cfg) -> 'Pending':
        return self.f(cfg)


class Pending:
    def __init__(self, use):
        self.get = use

    @contextmanager
    def use(self, cfg: 'CFG'):
        v = self.get(cfg)
        try:
            yield v
        finally:
            cfg.free(v.id)


class HS(Enum):
    RHS = astc.Load()
    LHS = astc.Store()


RHS = HS.RHS
LHS = HS.LHS
NONE = astc.Constant(None)


def name_of_id(id: str, hand_side: HS):
    return astc.Name(id=id, ctx=hand_side.value)


def equals(x: ast.expr, y: ast.expr):
    return astc.Compare(left=x, ops=[astc.Eq()], comparators=[y])


def same_as(x: ast.expr, y: ast.expr):
    return astc.Compare(left=x, ops=[astc.Is()], comparators=[y])


def assign_name(n: str, value: ast.expr):
    return astc.Assign(targets=[name_of_id(n, LHS)], value=value)


PREFIX = '_pysexpr_'
# name prefix after linear scan
PREFIX_OPT = '_pysexpropt_'


def prefixed(s, prefix=PREFIX):
    return '{}{}'.format(prefix, s)


class LiveInterval:
    start = None
    end = None


class RegPool(set):
    def __init__(self):
        set.__init__(self)
        self.cnt = 0

    def get_a_reg(self):
        if not self:
            self.cnt += 1
            n = prefixed(self.cnt, prefix=PREFIX_OPT)
        else:
            n = self.pop()
        return n


def linear_scan(lifetimes: Dict[str, LiveInterval]):
    # noinspection PyTypeChecker
    active = SortedDict()  # type: Dict[Tuple[int, str], LiveInterval]
    register_pool = RegPool()
    registers = {}
    # noinspection PyTypeChecker
    order_by_start = sorted(
        lifetimes.items(),
        key=lambda x: x[1].start)  # type: List[Tuple[str, LiveInterval]]
    for v, each in order_by_start:
        assert each.end is not None, 'Life circle of {} not initialized'
        assert each.start is not None, "Life circle of {} not disposed"

    def expire_old_intervals(i: LiveInterval):
        to_remove = []
        for key, j in active.items():
            _, varname = key
            if j.end >= i.start:
                return
            to_remove.append(key)
            register_pool.add(registers[varname])

    for varname, i in order_by_start:
        expire_old_intervals(i)
        registers[varname] = register_pool.get_a_reg()
        active[(i.end, varname)] = i
    return registers


class ReallocationVisitor(ast.NodeVisitor):
    def __init__(self, registers: Dict[str, str]):
        self.registers = registers

    def visit_Name(self, n):
        re_id = self.registers.get(n.id, None)
        if re_id is not None:
            n.id = re_id


class CFG:
    def __init__(self, temp_ns: set, loc: Tuple[int, int]):
        self.temp_names = temp_ns
        self.loc = loc
        self.builders = []
        self.lifetime = {}  # type: Dict[str, LiveInterval]

    def free(self, tmp: str):
        if tmp in self.lifetime:
            self.lifetime[tmp].end = len(self.builders)

    def alloc(self):
        n = prefixed(len(self.temp_names))
        self.temp_names.add(n)
        return n

    def build(self):
        """TODO: perform linear register allocation scan
        """
        registers = linear_scan(self.lifetime)
        realloc = ReallocationVisitor(registers)
        suite = sum((each() for each in self.builders), [])
        for each in suite:
            realloc.visit(each)
        return suite

    def add_stmt(self, s: ast.stmt):
        s.lineno, s.col_offset = self.loc
        s = [s]

        self.builders.append(lambda: s)

    def sub_cfg(self):
        return CFG(set(), self.loc)

    def start_life(self, n: str):
        life = self.lifetime[n] = LiveInterval()
        life.start = len(self.builders)

    def end_life(self, n: str):
        self.lifetime[n].end = len(self.builders)

    def push(self, expr: ast.expr, *, can_elim: bool) -> Pending:
        loc = self.loc

        def builder():
            for stmt in stmts:
                stmt.lineno, stmt.col_offset = loc
            return stmts

        if not can_elim:
            stmts = [astc.Expr(expr)]
            self.builders.append(builder)

            if not isinstance(expr, ast.Name):

                def run(cfg: CFG):
                    n = cfg.alloc()
                    cfg.start_life(n)

                    stmts[0] = assign_name(n, expr)
                    return name_of_id(n, RHS)
            else:

                def run(_):
                    return expr

        else:
            stmts = []
            self.builders.append(builder)

            if not isinstance(expr, ast.Name):

                def run(cfg: CFG):
                    n = cfg.alloc()
                    cfg.start_life(n)

                    stmts.append(assign_name(n, expr))
                    return name_of_id(n, RHS)
            else:

                def run(_):
                    return expr

        return Pending(run)


@contextmanager
def use_many(args: Iterable[Pending], cfg: CFG):
    vs = [arg.get(cfg) for arg in args]
    try:
        yield vs
    finally:
        for v in vs:
            cfg.free(v.id)


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

        with body.run(sub).use(sub) as body:
            # return TOP by default?
            # if so:
            sub.add_stmt(astc.Return(body))

        args = [astc.arg(arg=prefixed(n)) for n in args]
        args.append(astc.arg(arg='this'))
        args = astc.arguments(args=args, defaults=[NONE])

        body = sub.build()
        self.add_stmt(astc.FunctionDef(name=func_name, args=args, body=body))

        return self.push(name_of_id(func_name, RHS), can_elim=True)

    return run


def const(constant):
    @Term
    def run(self: CFG):
        return self.push(astc.Constant(constant), can_elim=True)

    return run


def dict(kv_pairs: List[Tuple[str, Term]]):
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
    @Term
    def run(self: CFG):
        args = (each.run(self) for each in args_)
        with ty_.run(self).use(self) as ty, use_many(args, self) as args:
            inst = astc.Dict(keys=[astc.Constant('.t')], values=[ty])
            args.append(inst)
            return self.push(astc.Call(func=ty, args=args), can_elim=True)

    return run


def var(n: str):
    @Term
    def run(self: CFG):
        return self.push(name_of_id(prefixed(n), RHS), can_elim=True)

    return run


def extern(n: str):
    @Term
    def run(self: CFG):
        return self.push(name_of_id(n, RHS), can_elim=True)

    return run


def tuple(*values_: Term):
    @Term
    def run(self: CFG):
        values = (each.run(self) for each in values_)
        with use_many(values, self) as values:
            ast_tuple = astc.Tuple(elts=values, ctx=RHS)
            return self.push(ast_tuple, can_elim=True)

    return run


def set_index(base_: Term, item_: Term, value_: Term):
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
    @Term
    def run(self: CFG):
        if not suite:
            return self.push(NONE, can_elim=True)
        *init, end = (each.run(self) for each in suite)
        with end.use(self) as end:
            return self.push(end, can_elim=True)

    return run


def for_range(n_: str, low_: Term, high_: Term, body: Term):
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
    @Term
    def run(self: CFG):
        n = prefixed(n_)
        with obj_.run(self).use(self) as obj:
            sub = self.sub_cfg()
            body_.run(sub)
            ast_for = astc.For(target=[name_of_id(n, LHS)],
                               iter=obj,
                               body=sub.build())
            self.add_stmt(ast_for)
            return self.push(NONE, can_elim=True)

    return run


def ite(cond_: Term, te: Term, fe: Term):
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
    @Term
    def run(self: CFG):
        self.loc = (line, column)
        return term.run(self)

    return run
