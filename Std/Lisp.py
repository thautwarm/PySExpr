from copy import copy

from ast import *


def makeLispFunc(sexpr_ArgNames, asts,  envWhenMake):
    DefaultArgs, argnameList = parseArguments(sexpr_ArgNames, envWhenMake)
    def pyFunc(kwargs, env):
        pack = dict()
        pack.update(env)
        default =  copy(DefaultArgs)
        kwargs = {name: (arg if arg is not None else maybeCallByName(default[name], env))
                  for name, arg in kwargs.items()}
        pack.update(kwargs)
        if not asts: return None
        ret = asts.pop()
        for ast in asts:
            ast_for_sexpr(ast, pack)
        return ast_for_sexpr(ret, pack)
    pyFunc.argnameList = argnameList
    return pyFunc

def maybeCallByName(maybeAst, env):
    return ast_for_sexpr(maybeAst, env) if isinstance(maybeAst, Ast) else maybeAst

def parseArguments(sexpr, env):
    if sexpr.name == 'Atom':
        return None, sexpr[0]
    else:
        default     = dict()
        argnameList = []
        sexpr = sexpr[1:-1]
        for elem in sexpr:
            if elem[0].name == 'Atom':
                """SExpr[Atom[<str>]]"""
                argnameList.append(elem[0][0])
            else:
                assert len(elem) is 2
                [[name]], value_ast = elem
                argnameList.append(name)
                default[name] = ast_for_sexpr(value_ast, env)

        return default, argnameList






