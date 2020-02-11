import ast_compat as astc
import ast
from contextlib import contextmanager


class Symbol:
    def __init__(self, s):
        self.s = s


class CFG:
    prefix = '_pysexpr__'

    def __init__(self, temp_ns: set, reuse: set, code: list):
        self.temp_names = temp_ns
        self.reuse = reuse
        self.code = code

    def free(self, tmp):
        if tmp not in self.temp_names:
            return
        self.temp_names.remove(tmp)
        self.reuse.add(tmp)

    def alloc(self):
        if self.reuse:
            n = self.reuse.pop()
        else:
            n = self.prefix + str(len(self.temp_names))
        self.temp_names.add(n)
        return n

    def build(self, s: ast.stmt):
        self.code.append(s)

    @classmethod
    def new(cls):
        return cls(set(), set(), [])


class UnboundTerm:
    def __init__(self, higher_rank_func):
        self.f = higher_rank_func

    def run(self, cfg):
        return self.f(cfg)

    @contextmanager
    def use(self, cfg: CFG):
        v = self.run(cfg)
        try:
            yield v
        finally:
            cfg.free(v)


class MBuiltin:
    pass


class MBuilder:
    def __init__(self, cls):
        self.cls = cls
        if issubclass(cls, MBuilder):

            def apply(*args):
                return cls(*args)
        else:

            def apply(*args):
                return call(cls, *args)

        self.apply = apply

    def __call__(self, *args):
        return self.apply(*args)


def use_many(args, cfg):
    return tuple(arg.use(cfg) for arg in args)


class Call(MBuiltin):
    def __new__(cls, func_, *args_):
        def term(cfg: CFG):
            tmp_n = cfg.alloc()
            with func_.use(cfg) as func, use_many(args_, cfg) as args:
                cfg.build(
                    astc.Assign(
                        targets=[astc.Name(id=tmp_n, ctx=astc.Store())],
                        value=astc.Call(func=func, args=list(args))))

                return ast.Name(id=tmp_n, ctx=astc.Load())

        return UnboundTerm(term)


call = Call


class Def(MBuiltin):
    def __new__(cls, name_: str, args_: list, body_, defaults_=None):
        def term(cfg: CFG):
            cfg_sub = CFG.new()
            if defaults_ is None:
                defaults = []
            else:
                defaults = defaults_

            args = astc.arguments(args=[astc.arg(arg) for arg in args_],
                                  defaults=defaults)

            if name_ is None:
                name = cfg.alloc()
            else:
                name = name_

            rhs = astc.Name(id=name_, ctx=astc.Load())
            cfg_sub.build(
                astc.FunctionDef(name=name, args=args,
                                 body=body_.run(cfg_sub)))
            return rhs

        return UnboundTerm(term)


class Assign(MBuiltin):
    def __new__(cls, name: str, rhs_):
        def term(cfg: CFG):
            lhs = astc.Name(id=name, ctx=astc.Store())
            with rhs_.use(cfg) as rhs:
                astc.Assign(targets=[lhs], value=rhs)
            return astc.Constant(None)

        return UnboundTerm(term)