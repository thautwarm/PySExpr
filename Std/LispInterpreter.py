#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 03:30:38 2017

@author: misakawa
"""

from Ruikowa.ErrorFamily import handle_error
from Ruikowa.ObjectRegex.MetaInfo import MetaInfo

from Std.lispParser import Stmt, token

parser = handle_error(Stmt)

class parse:
    @staticmethod
    def total(codes, meta = None):
        return parser(token(codes), meta if meta else MetaInfo())
    @staticmethod
    def partial(tokenized, meta = None):
        return parser(tokenized, meta if meta else MetaInfo())


class PyEnv:pass
class LispEnv:
    def __init__(self):
        self.NativeNamespace = [dict()]
        self.PyNamespace     = PyEnv()









