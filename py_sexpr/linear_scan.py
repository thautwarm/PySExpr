"""Implementation of infinite register based linear scan,
to optimize the allocations of temporary variables.
"""
from sortedcontainers import SortedDict
from py_sexpr.facility import prefixed, PREFIX_OPT
from typing import Dict, List, Tuple
__all__ = ['LiveInterval', 'linear_scan']


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
