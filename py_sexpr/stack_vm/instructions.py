from py_sexpr.stack_vm import instr_names
from py_sexpr.stack_vm.blockaddr import NamedLabel
from enum import Enum
from bytecode import Instr
from bytecode.instr import FreeVar, CellVar
from typing import Union, Type

MK_FN_HAS_DEFAULTS = 0x01
MK_FN_HAS_CLOSURE = 0x08


def LOAD_CONST(val):
    return Instr(instr_names.LOAD_CONST, val)


def LOAD_FAST(n):
    return Instr(instr_names.LOAD_FAST, n)


def LOAD_GLOBAL(n):
    return Instr(instr_names.LOAD_GLOBAL, n)


def STORE_GLOBAL(n):
    return Instr(instr_names.STORE_GLOBAL, n)


def COMPARE_OP(n):
    return Instr(instr_names.COMPARE_OP, n)


def RAISE_VARARGS(i):
    return Instr(instr_names.RAISE_VARARGS, i)


def LOAD_DEREF(n, cls: Union[Type[FreeVar], Type[CellVar]]):
    # will resolve free/cell var later
    return Instr(instr_names.LOAD_DEREF, cls(n))


def STORE_FAST(n):
    return Instr(instr_names.STORE_FAST, n)


def STORE_DEREF(n, cls: Union[Type[FreeVar], Type[CellVar]]):
    # will resolve free/cell var later
    return Instr(instr_names.STORE_DEREF, cls(n))


def LOAD_CLOSURE(n, cls: Union[Type[FreeVar], Type[CellVar]]):
    # will resolve free/cell var later
    return Instr(instr_names.LOAD_CLOSURE, cls(n))


def POP_TOP():
    return Instr(instr_names.POP_TOP)


def ROT3():
    return Instr(instr_names.ROT_THREE)


def ROT2():
    return Instr(instr_names.ROT_TWO)


def DUP():
    return Instr(instr_names.DUP_TOP)


def DUP2():
    return Instr(instr_names.DUP_TOP_TWO)


def POP_JUMP_IF_TRUE(i):
    return Instr(instr_names.POP_JUMP_IF_TRUE, i)


def POP_JUMP_IF_FALSE(i):
    return Instr(instr_names.POP_JUMP_IF_FALSE, i)


def JUMP_ABSOLUTE(i):
    return Instr(instr_names.JUMP_ABSOLUTE, i)


def BINARY(bin_op):
    return Instr('BINARY_' + bin_op.name)


def INPLACE_BINARY(bin_op):
    return Instr('INPLACE_' + bin_op.name)


def UNARY(u_op):
    return Instr('UNARY_' + u_op.name)


def UNPACK_SEQUENCE(n: int):
    return Instr(instr_names.UNPACK_SEQUENCE, n)


def LOAD_ATTR(n):
    return Instr(instr_names.LOAD_ATTR, n)


def STORE_ATTR(n):
    return Instr(instr_names.STORE_ATTR, n)


def STORE_SUBSCR():
    return Instr(instr_names.STORE_SUBSCR)


def CALL_FUNCTION(n: int):
    return Instr(instr_names.CALL_FUNCTION, n)


def BUILD_LIST(n):
    return Instr(instr_names.BUILD_LIST, n)


def BUILD_TUPLE(n):
    return Instr(instr_names.BUILD_TUPLE, n)


def BUILD_MAP(n):
    return Instr(instr_names.BUILD_MAP, n)


def BUILD_MAP_UNPACK(n):
    return Instr(instr_names.BUILD_MAP_UNPACK, n)


def BUILD_CONST_KET_MAP(n):
    return Instr(instr_names.BUILD_CONST_KEY_MAP, n)


def LIST_APPEND(i):
    return Instr(instr_names.LIST_APPEND, i)


def RETURN_VALUE():
    return Instr(instr_names.RETURN_VALUE)


def MAKE_FUNCTION(flag):
    assert isinstance(flag, int)
    return Instr(instr_names.MAKE_FUNCTION, flag)


def MAKE_CLOSURE(argc):
    assert isinstance(argc, int)
    return Instr(instr_names.MAKE_CLOSURE, argc)


def PRINT_EXPR():
    return Instr(instr_names.PRINT_EXPR)


def GET_ITER():
    return Instr(instr_names.GET_ITER)


def FOR_ITER(l: NamedLabel):
    return Instr(instr_names.FOR_ITER, l)


# for Python 3.8-
def PUSH_BLOCK(l: NamedLabel):
    return Instr(instr_names.SETUP_LOOP, l)


def POP_BLOCK():
    return Instr(instr_names.POP_BLOCK)


def _auto(*, _cnt=[0]):
    r = _cnt[0]
    _cnt[0] += 1
    return r


class UOp(Enum):
    POSITIVE = _auto()
    NEGATIVE = _auto()
    NOT = _auto()
    INVERT = _auto()
    pass


class BinOp(Enum):
    POWER = _auto()
    MULTIPLY = _auto()
    MATRIX_MULTIPLY = _auto()
    FLOOR_DIVIDE = _auto()
    TRUE_DIVIDE = _auto()
    MODULO = _auto()
    ADD = _auto()
    SUBTRACT = _auto()
    SUBSCR = _auto()
    LSHIFT = _auto()
    RSHIFT = _auto()
    AND = _auto()
    XOR = _auto()
    OR = _auto()
