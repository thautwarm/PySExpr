"""This module preserved for further advanced features, like `Label as Value`, switch expressions.
"""
from bytecode import Label
import attr
__all__ = ['NamedLabel']

WHY_CONTINUE = 0x0020


@attr.s(order=True, frozen=True)
class NamedLabel(Label):
    name = attr.ib()  # type: object
