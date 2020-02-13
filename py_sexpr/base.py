import ast_compat as astc
import ast
from contextlib import contextmanager
from typing import Dict, Tuple, Iterable
from py_sexpr.facility import *
from py_sexpr.linear_scan import LiveInterval, linear_scan


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
        """Free a temporary variable,
        accept the name string.
        """
        if tmp in self.lifetime:
            self.lifetime[tmp].end = len(self.builders)

    def alloc(self):
        """allocate a temporary variable,
        return the name string.
        """
        n = prefixed(len(self.temp_names))
        self.temp_names.add(n)
        return n

    def build(self):
        """Build the final AST suite from current CFG.
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
