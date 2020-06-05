DONE = "DONE"
import collections
import sys
import types
import attr
import operator
import enum


def scheduling(application):
    coroutines = [application]
    append = coroutines.append
    pop = coroutines.pop
    last = None
    while coroutines:
        end = coroutines[-1]
        try:
            value = end.send(last)
            if isinstance(value, types.GeneratorType):
                append(value)
                last = None
            else:
                last = value
                pop()
        except StopIteration as e:
            pop()
            last = e.value
    return last


@attr.s
class Lit:
    value = attr.ib()

    def accept(self, visitor):
        return visitor.lit(self)


class BinOp(enum.Enum):
    Add = "+"
    Sub = "-"
    Mul = "*"
    TrueDiv = "/"


@attr.s
class Bin:
    op = attr.ib()
    l = attr.ib()
    r = attr.ib()

    def accept(self, visitor):
        return visitor.bin(self)


class Interpolator:
    def eval(self, e):
        return (yield e.accept(self))

    def lit(self, l: Lit):
        # value = yield l.value
        return l.value

    def bin(self, bop: Bin):
        ops = {
            BinOp.Add: operator.add,
            BinOp.Sub: operator.sub,
            BinOp.Mul: operator.mul,
            BinOp.TrueDiv: operator.truediv,
        }
        lvalue = yield self.eval(bop.l)
        rvalue = yield self.eval(bop.r)
        return ops[bop.op](lvalue, rvalue)


def fact(n):
    if n == 0:
        return 1
    else:
        value = yield fact, n - 1
        return n * value


def sumn(n):
    if n == 0:
        return 0
    else:
        value = yield sumn(n - 1)
        return n + value


one_plus_one = Bin(BinOp.Add, Lit(1), Lit(1))


def large_sum(depth):
    if depth < 1:
        raise ValueError("Depth should >= 1")
    result = Lit(1)
    for _ in range(depth - 1):
        result = Bin(BinOp.Add, Lit(1), result)
    return result


itp = Interpolator()
# print(one_plus_one)
print(scheduling(itp.eval(Lit(1))))
print(scheduling(itp.eval(one_plus_one)))
print(scheduling(itp.eval(large_sum(10))))
print(scheduling(itp.eval(large_sum(100))))
print(scheduling(itp.eval(large_sum(1000))))
print(scheduling(itp.eval(large_sum(10000))))

# def trampoline(g):
#     stack = [g]
#     value = None
#     while len(stack) > 0:
#         try:
#             while len(stack) > 0:
#                 to_run = stack.pop()
#                 print(to_run)
#                 if(to_run is None):
#                     print(value)
#                     print(stack)
#                 cont = next(to_run, value)
#                 stack.append(to_run)
#                 stack.append(cont)
#         except StopIteration as e:
#             value = e.value
#     return value


# print(scheduling(sumn(0)))

# t = Trampoline()
# t.add(fact(10))
# print(t.run())
