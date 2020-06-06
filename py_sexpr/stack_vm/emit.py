import attr
import bytecode as BC
from typing import List, Dict, Callable, Optional, Set, Union
from enum import Enum
from functools import lru_cache
from py_sexpr.stack_vm import instructions as I
from py_sexpr.stack_vm.blockaddr import NamedLabel, merge_labels
from sys import version_info
import types

PY38 = version_info >= (3, 8)
PY35 = version_info < (3, 6)
_app = lambda arg: lambda f: f(arg)

RECORD_TYPE_FIELD = ".t"


def scheduling(application):
    GeneratorType = types.GeneratorType
    coroutines = [application]
    append = coroutines.append
    pop = coroutines.pop
    last = None
    while coroutines:
        end = coroutines[-1]
        try:
            value = end.send(last)
            if isinstance(value, GeneratorType):
                append(value)
                last = None
            else:
                last = value
                pop()
        except StopIteration as e:
            if isinstance(e.value, GeneratorType):
                append(e.value)
                last = None
            else:
                pop()
                last = e.value
    return last


class NamedObj:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return self.n


def _new_unique_label(s):
    """create a label whose identity is its address.
    """

    # noinspection PyArgumentList
    return NamedLabel(NamedObj(s))


def _new_structural_label(s):
    """create a label whose identity is its name.
    """

    # noinspection PyArgumentList
    return NamedLabel(s)


class SymType(Enum):
    cell = "cell"
    glob = "global"
    bound = "bound"


@lru_cache()
def glob_sym(n: str):
    return Sym(n, SymType.glob)


class Sym:
    # if shared to other function objects
    name = None  # type: str
    ty = None  # type: SymType
    scope = None  # type: Optional['ScopeSolver']

    def __init__(self, name: str, ty: SymType, scope=None):
        self.name = name
        self.ty = ty
        self.scope = scope


class Analysed:
    """
    An analysed scope, which provides you
    - `free`: free variables captured from outer scopes.
    - `bound`: bound variables created in current scope.
    """

    syms_free = None  # type: Dict[str, Sym]
    syms_bound = None  # type: Dict[str, Sym]


def _set_lineno(i: int, f):
    def apply():
        instructions = f()
        Instr = BC.Instr
        for instr in instructions:
            if isinstance(instr, Instr):
                instr.lineno = i
        return instructions

    return apply


@attr.s
class ScopeSolver:
    """We use a simple scoping rule, that all assignments enter symbols
    locally, i.e., free variables are readonly beyond where it's defined.
    """

    n_enter = attr.ib()  # type: Set[str]
    n_require = attr.ib()  # type:  Set[str]
    parent = attr.ib()  # type: Optional['ScopeSolver']
    children = attr.ib()  # type: List['ScopeSolver']
    output = attr.ib()  # type: Analysed

    @classmethod
    def outermost(cls):
        return ScopeSolver(set(), set(), None, [], Analysed())

    def sub_scope(self):
        new = ScopeSolver(set(), set(), self, [], Analysed())
        self.children.append(new)
        return new

    def enter(self, n: str):
        self.n_enter.add(n)

    def require(self, n: str):
        self.n_require.add(n)

    def _get_sym(self, n):
        sym = self.output.syms_bound.get(n)
        if sym:
            return sym
        if not self.parent:
            return glob_sym(n)
        return self.parent._get_sym(n)

    def resolve(self):
        n_enter = self.n_enter
        analysed = self.output
        if self.parent is None:
            analysed.syms_bound = {}
        else:
            analysed.syms_bound = {k: Sym(k, SymType.bound, analysed) for k in n_enter}
        analysed.syms_free = {}

        n_require = self.n_require.difference(n_enter)
        for n in n_require:
            sym = self._get_sym(n)
            if sym and sym.ty is not SymType.glob:
                sc = self
                sym.ty = SymType.cell
                scope = sym.scope

                # add free variable `sym` to each scope
                # between `sym`'s define scope and use scope.
                while scope is not sc.output:
                    if n in sc.output.syms_free:
                        break

                    sc.output.syms_free[n] = sym
                    sc = sc.parent

        for child in self.children:
            child.resolve()


@attr.s
class SharedState:
    doc = attr.ib()  # type: str
    line = attr.ib()  # type: int
    filename = attr.ib()  # type: str

    def copy(self):
        return SharedState(self.doc, self.line, self.filename)


@attr.s
class Builder:
    sc = attr.ib()  # type: ScopeSolver
    builders = attr.ib()  # type: List[Callable[[Analysed], List[BC.Instr]]]
    st = attr.ib()  # type: SharedState

    def __lshift__(self, other: Callable[[], List[Union[BC.Instr, BC.Label]]]):

        self.builders.append(_set_lineno(self.st.line, other))

    def build(self):
        # TODO: detect why `sum(..., [])` not work here
        seq = []
        for b in self.builders:
            seq.extend(b())

        n = len(seq)
        Instr = BC.Instr

        # remove redundant load/pop pairs
        def _build(seq):
            i = 0
            n = len(seq)
            while i < n:
                each = seq[i]
                if isinstance(each, Instr) and each.name.startswith("LOAD_"):
                    nxt = i + 1
                    if nxt < n:
                        nxt_instr = seq[nxt]
                        if isinstance(nxt_instr, Instr) and nxt_instr.name == "POP_TOP":
                            i = nxt + 1
                            continue
                yield each
                i += 1

        while True:
            seq = list(_build(seq))
            if len(seq) == n:
                break
            n = len(seq)
        return seq

    def inside(self):
        return Builder(self.sc.sub_scope(), [], self.st.copy(),)

    def eval(self, term):
        if isinstance(term, tuple):
            hd, *tl = term
            if hd == "eval":
                return (yield self.eval(*tl))
            else:
                return getattr(self, hd)(*tl)

        return self.const(term)

    def eval_all(self, terms):
        eval = self.eval
        for each in terms:
            yield eval(each)

    def const(self, value):
        def build():
            return [I.LOAD_CONST(value)]

        self << build

    def call(self, f, *args):
        yield self.eval(f)
        yield self.eval_all(args)
        n = len(args)

        def build():
            i = I.CALL_FUNCTION(n)
            return [i]

        self << build

    def var(self, n: str):
        analysed = self.sc.output
        self.sc.require(n)

        def build():
            sym = analysed.syms_bound.get(n)
            if sym:
                if sym.ty is SymType.cell:
                    i = I.LOAD_DEREF(n, I.CellVar)
                else:
                    i = I.LOAD_FAST(n)
                return [i]
            if n in analysed.syms_free:
                i = I.LOAD_DEREF(n, I.FreeVar)
            else:
                i = I.LOAD_GLOBAL(n)
            return [i]

        self << build

    def tuple(self, *elts):
        yield self.eval_all(elts)
        n = len(elts)
        self << (lambda: [I.BUILD_TUPLE(n)])

    def record(self, *kwargs):
        n = len(kwargs)
        if not kwargs:
            self << (lambda: [I.BUILD_MAP(0)])
        elif PY35:
            eval = self.eval
            for key, val in kwargs:
                yield eval(key)
                yield eval(val)
            self << (lambda: [I.BUILD_MAP(n)])
        else:
            keys, vals = zip(*kwargs)
            yield self.eval_all(vals)
            self.const(keys)
            self << (lambda: [I.BUILD_CONST_KET_MAP(n)])

    def lens(self, l, r):
        yield self.eval(l)
        yield self.eval(r)
        self << (lambda: [I.BUILD_MAP_UNPACK(2)])

    def assign_star(self, n: str, v):
        yield self.eval(v)
        self._bind(n, True)
        self << (lambda: [I.LOAD_CONST(None)])

    def assign(self, n: str, v):
        yield self.eval(v)
        self._bind(n, False)
        self << (lambda: [I.LOAD_CONST(None)])

    def get_attr(self, val, n: str):
        yield self.eval(val)
        self << (lambda: [I.LOAD_ATTR(n)])

    def set_attr(self, base, n: str, val):
        yield self.eval(val)
        yield self.eval(base)
        self << (lambda: [I.STORE_ATTR(n), I.LOAD_CONST(None)])

    def get_item(self, base, item: str):
        yield self.eval(base)
        yield self.eval(item)

        self << (lambda: [I.BINARY(I.BinOp.SUBSCR)])

    def set_item(self, base, item, val):
        yield self.eval(val)
        yield self.eval(base)
        yield self.eval(item)
        self << (lambda: [I.STORE_SUBSCR(), I.LOAD_CONST(None)])

    def new(self, ty, *args):
        """
        Basically, it's
            new(ty, *args) ==
                this = ty(*args, {})
                this['.t'] = ty
        This is efficient and avoids redundant
        register allocation, hence I'm quite proud
        of this idea :)
        """
        yield self.eval(ty)

        # build this object
        self << (lambda: [I.DUP()])

        yield self.eval_all(args)
        n = len(args) + 1

        # initialize this object
        self << (
            lambda: [
                I.BUILD_MAP(0),
                I.CALL_FUNCTION(n),
                I.DUP(),
                I.ROT3(),
                I.LOAD_CONST(RECORD_TYPE_FIELD),
                I.STORE_SUBSCR(),
            ]
        )

    def un(self, op: I.UOp, term):
        """emit unary operation"""
        yield self.eval(term)
        self << (lambda: [I.UNARY(op)])

    def bin(self, l, op: I.BinOp, r):
        """emit binary operation"""
        yield self.eval(l)
        yield self.eval(r)
        self << (lambda: [I.BINARY(op)])

    def cmp(self, l, op: BC.Compare, r):
        yield self.eval(l)
        yield self.eval(r)
        self << (lambda: [I.COMPARE_OP(op)])

    def _bind(self, n: str, bound: bool):
        analysed = self.sc.output
        if bound:
            self.sc.enter(n)
        else:
            self.sc.require(n)

        def build():
            sym = analysed.syms_bound.get(n)
            if sym:
                if sym.ty is SymType.cell:
                    i = I.STORE_DEREF(n, I.CellVar)
                else:
                    i = I.STORE_FAST(n)
                return [i]
            if n in analysed.syms_free:
                i = I.STORE_DEREF(n, I.FreeVar)
            else:
                i = I.STORE_GLOBAL(n)
            return [i]

        self << build

    def block(self, *suite):
        if not suite:
            return self.const(None)
        *init, end = suite
        for each in init:
            yield self.eval(each)
            self << (lambda: [I.POP_TOP()])
        yield self.eval(end)

    def doc(self, doc: str, it):
        self.st.doc = doc
        return (yield self.eval(it))

    def line(self, line: int, it):
        self.st.line = line
        return (yield self.eval(it))

    def filename(self, fname: str, it):
        self.st.filename = fname
        return (yield self.eval(it))

    def ite(self, cond, true_clause, false_clause):
        label_true = _new_unique_label("if.true")
        label_end = _new_unique_label("if.end")

        yield self.eval(cond)
        self << (lambda: [I.POP_JUMP_IF_TRUE(label_true)])
        yield self.eval(false_clause)
        self << (lambda: [I.JUMP_ABSOLUTE(label_end), label_true])
        yield self.eval(true_clause)
        self << (lambda: [label_end])

    def for_in(self, n: str, seq, body):
        label_end = _new_unique_label("end.loop")
        label_iter = _new_unique_label("iter.loop")

        yield self.eval(seq)
        self << (lambda: [I.GET_ITER(), label_iter, I.FOR_ITER(label_end)])

        self._bind(n, bound=False)
        yield self.eval(body)
        self << (
            lambda: [
                I.POP_TOP(),
                I.JUMP_ABSOLUTE(label_iter),
                label_end,
                I.LOAD_CONST(None),
            ]
        )

    def ret(self, v):
        yield self.eval(v)
        self << (lambda: [I.RETURN_VALUE(), I.LOAD_CONST(None)])

    def throw(self, v):
        yield self.eval(v)
        self << (lambda: [I.RAISE_VARARGS(1)])
        self.const(None)

    def loop(self, cond, body):
        """
        Note, the value of `body` in the last iteration will be returned.
        e.g.,
            z = 2
            f = while z < 5 {
                z += z
                z
            }
        The value of `f` is 8
        """
        label_setup = _new_unique_label("while.setup")
        label_end = _new_unique_label("while.end")

        self << (lambda: [I.LOAD_CONST(None), label_setup])
        yield self.eval(cond)
        self << (lambda: [I.POP_JUMP_IF_FALSE(label_end), I.POP_TOP()])
        yield self.eval(body)
        self << (lambda: [I.JUMP_ABSOLUTE(label_setup), label_end])

    def func(self, args: List[str], body, name: str = None, defaults: list = ()):
        line = self.st.line
        filename = self.st.filename
        doc = self.st.doc
        mk_fn_flag = 0
        anonymous = True
        if name:
            anonymous = False
            self.sc.enter(name)
        else:
            name = "lambda:{}".format(line)

        if defaults:  # if any default arguments
            if PY35:
                mk_fn_flag = len(defaults)
                for each in defaults:
                    yield self.eval(each)
            else:
                mk_fn_flag |= I.MK_FN_HAS_DEFAULTS

                for each in defaults:
                    yield self.eval(each)
                n_defaults = len(defaults)

                def build_defaults():
                    i = I.BUILD_TUPLE(n_defaults)
                    i.lineno = line
                    return [i]

                self << build_defaults
        sub = self.inside()

        # visit arguments
        sub_sc_enter = sub.sc.enter
        for each in args:
            sub_sc_enter(each)

        yield sub.eval(body)

        analysed = self.sc.output

        def build_mk_func():
            nonlocal mk_fn_flag
            sub_a = sub.sc.output
            ins = []
            frees = list(sub_a.syms_free)

            # get all cell names from bound variables
            cells = [n for n, sym in sub_a.syms_bound.items() if sym.ty is SymType.cell]

            if frees:  # handle closure conversions
                if not PY35:
                    mk_fn_flag |= I.MK_FN_HAS_CLOSURE

                for n in frees:
                    if n in analysed.syms_bound:
                        var_type = I.CellVar
                    else:
                        var_type = I.FreeVar
                    ins.append(I.LOAD_CLOSURE(n, var_type))
                ins.append(I.BUILD_TUPLE(len(frees)))

            # create code object of subroutine
            instructions = sub.build()
            py_code = make_code_obj(
                name, filename, line, doc, args, frees, cells, instructions
            )
            ins.extend(
                [
                    I.LOAD_CONST(py_code),
                    I.LOAD_CONST(name),
                    I.MAKE_CLOSURE(mk_fn_flag)
                    if PY35 and frees
                    else I.MAKE_FUNCTION(mk_fn_flag),
                ]
            )

            # if not anonymous function,
            # we shall assign the function to a variable
            if not anonymous:
                fn_sym = analysed.syms_bound.get(name)
                if not fn_sym:
                    store = I.STORE_GLOBAL(name)
                elif fn_sym.ty is SymType.bound:
                    store = I.STORE_FAST(name)
                elif fn_sym.ty is SymType.cell:
                    store = I.STORE_DEREF(name, I.CellVar)
                else:
                    raise ValueError
                ins.extend([I.DUP(), store])

            return ins

        self << build_mk_func


def make_code_obj(
    name: str,
    filename: str,
    lineno: int,
    doc: str,
    args: List[str],
    frees: List[str],
    cells: List[str],
    instructions: List[BC.Instr],
):
    """Create code object from given metadata and instructions
    """
    if not instructions:
        instructions.append(I.LOAD_CONST(None))
    instructions.append(I.RETURN_VALUE())
    instructions = list(merge_labels(instructions))

    bc_code = BC.Bytecode(instructions)
    bc_code.name = name
    bc_code.filename = filename
    bc_code.first_lineno = lineno
    bc_code.docstring = doc
    bc_code.argnames.extend(args)
    bc_code.argcount = len(bc_code.argnames)
    bc_code.freevars.extend(frees)
    bc_code.cellvars.extend(cells)
    stack_size = bc_code.compute_stacksize()

    c_code = bc_code.to_concrete_bytecode()
    c_code.flags = BC.flags.infer_flags(c_code)
    py_code = c_code.to_code(stacksize=stack_size)
    return py_code


def module_code(
    sexpr,
    name: str = "<unknown>",
    filename: str = "<unknown>",
    lineno: int = 1,
    doc: str = "",
):
    """Create a module's code object from given metadata and s-expression.
    """
    module_builder = Builder(
        ScopeSolver.outermost(), [], SharedState(doc, lineno, filename)
    )

    # incompletely build instruction
    scheduling(module_builder.eval(sexpr))

    # resolve symbols, complete building requirements
    module_builder.sc.resolve()

    # complete building requirements
    instructions = module_builder.build()
    code = make_code_obj(name, filename, lineno, doc, [], [], [], instructions)
    return code
