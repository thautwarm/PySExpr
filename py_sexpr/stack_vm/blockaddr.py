"""This module preserved for further advanced features, like `Label as Value`, switch expressions.
"""
from bytecode import Label, Instr
from typing import List

__all__ = ["NamedLabel", "merge_labels"]

WHY_CONTINUE = 0x0020


class NamedLabel(Label):
    name = None  # type: object

    def __init__(self, name: object):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, NamedLabel) and self.name == other.name

    def __hash__(self):
        return 114514 ^ hash(self.name)


def merge_labels(xs: List[Instr]):
    equals_to = {}
    last_label = None

    for each in xs:
        if isinstance(each, Label):
            if last_label:
                equals_to[each] = last_label
            else:
                equals_to[each] = each
                last_label = each
        else:
            last_label = None
    last_label = None
    for each in xs:
        if isinstance(each, Label):
            each = equals_to[each]
            if each is not last_label:
                last_label = each
            else:
                continue
        else:
            last_label = None
            if isinstance(each, Instr) and each.has_jump():
                each.arg = equals_to[each.arg]
        yield each
