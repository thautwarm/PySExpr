"""This module preserved for further advanced features, like `Label as Value`, switch expressions.
"""
from bytecode import Label
__all__ = ['NamedLabel']

WHY_CONTINUE = 0x0020


class NamedLabel(Label):
    name = None  # type: object

    def __init__(self, name: object):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, NamedLabel) and self.name == other.name

    def __hash__(self):
        return 114514 ^ hash(self.name)
