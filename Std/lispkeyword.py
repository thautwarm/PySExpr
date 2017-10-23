
from Lisp import *

def define(arg_list, env):
    name, arguments, *stmts = arg_list
    env[name] = makeLispFunc(arguments, stmts, env)
    return env[name]

def setq(arg_list, env):
    name, value_ast = arg_list
    env[name] = ast_for_sexpr(value_ast, env)

def If(arg_list, env):
    test, if_do, else_do = arg_list
    if ast_for_sexpr(test, env):
        return ast_for_sexpr(if_do, env)
    else:
        return ast_for_sexpr(else_do, env)





