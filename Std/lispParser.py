
from Ruikowa.ObjectRegex.Node import Ref, AstParser, SeqParser, LiteralParser, CharParser

namespace     = globals()
recurSearcher = set()
Atom = AstParser([LiteralParser('[^\(\)\s\`]+', name='\'[^\(\)\s\`]+\'', isRegex = True)], name = 'Atom')
SExpr = AstParser([Ref('Atom')],[Ref('Quote')],[CharParser('(', name='\'(\''),SeqParser([SeqParser([Ref('NEWLINE')]),SeqParser([Ref('SExpr')]),SeqParser([Ref('NEWLINE')])]),CharParser(')', name='\')\'')], name = 'SExpr', toIgnore = [set(), {"'\\n'"}])
Quote = AstParser([CharParser('`', name='\'`\''),Ref('SExpr')], name = 'Quote')
NEWLINE = CharParser('\n', name = 'NEWLINE')
Stmt = AstParser([SeqParser([SeqParser([Ref('NEWLINE')]),SeqParser([Ref('SExpr')]),SeqParser([Ref('NEWLINE')])])], name = 'Stmt', toIgnore = [set(), {"'\\n'"}])
Atom.compile(namespace, recurSearcher)
SExpr.compile(namespace, recurSearcher)
Quote.compile(namespace, recurSearcher)
Stmt.compile(namespace, recurSearcher)
