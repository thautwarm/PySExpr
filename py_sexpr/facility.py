"""Utilities for building Python ASTs
"""
import ast_compat as astc
import ast
from enum import Enum

__all__ = [
    'HS', 'RHS', 'LHS', 'NONE', 'name_of_id', 'equals', 'same_as',
    'assign_name', 'prefixed', 'PREFIX_OPT'
]


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
