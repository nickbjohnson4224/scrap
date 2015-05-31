import json

class LexerError(Exception):
    
    def __init__(self, pos, lexeme):
        self.pos = pos
        self.lexeme = lexeme

class Token(object):

    def __init__(self, ttype, lexeme, start, end):
        self.ttype = ttype
        self.lexeme = lexeme
        self.start = start
        self.end = end
        self.value = None

    def __repr__(self):
        if self.value is not None:
            return '%s(%r)' % (self.ttype, self.value)
        elif self.lexeme is not None:
            return '%s(%s)' % (self.ttype, json.dumps(self.lexeme))
        else:
            return self.ttype

# operators that can be formed into constructs like +=
_ASSIGN_BINOPS = set([
    'PLUS',
    'MINUS',
    'DSTAR',
    'STAR',
    'DDIV',
    'DIV',
    'MOD',
    'BITAND',
    'BITOR',
    'BITXOR',
    'BITNOT',
    'SHIFTUR',
    'SHIFTAR',
    'SHIFTL',
    'CAT'
])

_KEYWORDS = {
    'if': 'IF',
    'elif': 'ELIF',
    'else': 'ELSE',
    'for': 'FOR',
    'in': 'IN',
    'while': 'WHILE',
    'do': 'DO',
    'return': 'RETURN',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'def': 'DEF',
    'function': 'FUNCTION',
    'import': 'IMPORT',
    'assert': 'ASSERT',
    'pragma': 'PRAGMA',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT'
}

def lex1(tables, input, source=None):
    line = 0
    col = 0
    pos = (source, 0, 0)

    state = 1
    token_buffer = []
    token_start = (0, 0)

    input_tab = tables['input']
    trans_tab = tables['trans']
    ttype_tab = tables['output']

    for symbol in input:

        while 1:
            # update DFA state
            next_state = trans_tab[state][input_tab.get(symbol, 0)]
            if next_state == 0:
                lexeme = ''.join(token_buffer)
                ttype = ttype_tab[state]
            
                if ttype == None:
                    raise LexerError(pos, lexeme)
            
                yield Token(ttype, lexeme, token_start, lastpos)
                
                state = 1
                token_buffer = []
                token_start = pos
            else:
                state = next_state
                token_buffer.append(symbol)
                break
        
        # keep track of line position
        if symbol == '\n':
            line += 1
            col = 0
        else:
            col += 1
        lastpos = pos
        pos = (source, line, col)

    lexeme = ''.join(token_buffer)
    ttype = ttype_tab[state]

    if ttype == None:
        raise LexerError(pos, lexeme)
        
    yield Token(ttype, lexeme, token_start, lastpos)

def lex2(token_stream):
    # second level of lexer processing
    # - remove whitespace and comments
    # - identify keywords
    # - combine update operators (+=)
    
    peek = None
    while True:
        if peek == None:
            token = next(token_stream)
        else:
            token = peek
            peek = None
        
        if token.ttype == 'WHITE':
            continue

        elif token.ttype == 'COMMENT':
            continue

        elif token.ttype == 'NAME':
            # check for keywords
            if token.lexeme in _KEYWORDS:
                token.ttype = _KEYWORDS[token.lexeme]

        elif token.ttype in _ASSIGN_BINOPS:
            # form update ops (like +=)
            peek = next(token_stream)
            if peek.ttype == 'ASSIGN':
                token.ttype = 'ASSIGN_' + token.ttype
                token.end = peek.end
                token.lexeme += peek.lexeme
                peek = None

        yield token

def lex3(token_stream):
    # third level of lexer processing
    # - parse string literals
    # - parse numeric literals
    # - strip unneeded lexemes
    
    for token in token_stream:
        
        if token.ttype == 'NAME':
            yield token
        elif token.ttype == 'HEXLIT':
            token.ttype = 'NUMBER'
            token.value = int(token.lexeme[2:], 16)
            yield token
        elif token.ttype == 'INTLIT':
            token.ttype = 'NUMBER'
            token.value = int(token.lexeme, 10)
            yield token
        elif token.ttype == 'FLTLIT':
            token.ttype = 'NUMBER'
            token.value = float(token.lexeme)
            yield token
        elif token.ttype == 'STRLIT':

            first_squote = token.lexeme.find("'")
            first_dquote = token.lexeme.find('"')

            if first_squote == -1:
                prefix_end = first_dquote
            elif first_dquote == -1:
                prefix_end = first_squote
            else:
                prefix_end = min(first_dquote, first_squote)

            prefix, rest = token.lexeme[:prefix_end], token.lexeme[prefix_end:]
            if rest[0] == "'":
                if rest[1:3] == "''":
                    body = rest[3:-3]
                else:
                    body = rest[1:-1]
            elif rest[0] == '"':
                if rest[1:3] == '""':
                    body = rest[3:-3]
                else:
                    body = rest[1:-1]
            
            if prefix:
                token1 = Token('STRPREFIX', prefix, token.start, token.end)
                token1.value = prefix
                yield token1

            token.ttype = 'RAWSTR'
            token.value = body
            yield token
        else:
            # strip all other lexemes
            token.lexeme = None
            yield token

def lex(tables, input, source=None):
    for token in lex3(lex2(lex1(tables, input, source=source))):
        yield token
