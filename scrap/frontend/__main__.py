import json
import sys
import os

import lexer

import scrap.genutil.lexer_tables as lt

def main(source_path):
    currpath = os.path.realpath(__file__)
    dfa = lt.nfa_to_dfa(*lt.compile_lexerdef(os.path.join(os.path.dirname(currpath), '../res/lexerdef.json')))
    tables = {
        'input': dfa[0],
        'trans': dfa[1],
        'output': dfa[2]
    }

    source = open(source_path).read()
    for token in lexer.lex(tables, source, source_path):
        print token,

if __name__ == '__main__':
    main(*sys.argv[1:])
