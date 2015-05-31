# This file implements the lexer generator for Scrap.
#
# There are two passes in this generation. First, the lexer definition is read
# in as JSON, which represents regular expressions for each token class. (This
# representation is defined below.) These regular expressions are each compiled
# to NFAs. Second, the union of all the NFAs is compiled to a single DFA,
# in table form, which is then emitted as JSON (later it might be pickled). 
# This DFA table is used by the lexer to do actual tokenization.
#

from collections import defaultdict
import json
import sys

#
# Regular expressions as JSON
#
# JSON lists are used like S-expressions to represent regular expression
# operators with a prefix notation. This eliminates the need to write a
# parser to get the parser generator working.
# 
# i.e. ["hello", "world", ["x", "y"]] is like (hello "world" (x "y"))
#
# The basic regex operators are, of course: "cat", "alt", and "star",
# for concatenation, alternation, and Kleene closure, respectively.
#
# Extended operators "opt" and "plus" are implemented by the following
# rewrites:
# 
# ["opt", foo] => ["alt", "", foo]
# ["plus", foo] => ["cat" foo, ["star" foo]]
#
# Literal strings of length 1 represent single symbols. Literal strings
# of length 0 represent epsilon transitions. Literal strings of length
# greater than 1 are implicit concatenations of their symbols.
#
# The two operators "range" and "class" are used to represent large
# alternations of single symbols. "range" takes a mixture of single
# symbols and pairs, which represent ranges through the ASCII encoding
# space. "class" can be used with the following fixed argument strings:
#
# ["class", "space"] => ["alt", " ", "\t", "\r", "\n"]
# ["class", "digit"] => ["range", ["0", "9"]]
# ["class", "alpha"] => ["range", ["a", "z"], ["A", "Z"]]
# ["class", "alnum"] => ["range", ["a", "z"], ["A", "Z"], ["0", "9"]]
# ["class", "name'] => ["range", ["a", "z"], ["A", "Z"], ["0", "9"], "_"]
# ["class", "!x"] => ["range", ["\0", x-1], [x+1, "\x7f"]]
#
# Why define classes like this? Because if we ever add Unicode support,
# it'll make things a lot easier, because we can extend "alphabet" or
# "alphanumeric" character classes to include the correct extended symbols.
#

#
# NFA representation
#
# An NFA is a pair (start_state, [outgoing_trans]).
#
# All of the transitions in [outgoing_trans] have None as tails.
#

class NFAState(object):

    next_id = 0
    
    def __init__(self, outputs=[]):
        self.outputs = list(outputs)
        self.transitions = defaultdict(list)
        self._id = NFAState.next_id
        NFAState.next_id += 1

    def follow(self, symbol):
        return (t.tail for t in self.transitions.get(symbol, []) if t.tail)

class NFATransition(object):
    
    def __init__(self, head, tail, symbol):
        self.head = head
        self.tail = tail
        self.symbol = symbol

def add_nfa_transition(head, tail, symbol):
    t = NFATransition(head, tail, symbol)
    head.transitions[symbol].append(t)

def regex_to_nfa(regex, outputs=None):
    """Compile a JSON regex to an NFA."""

    if outputs:
        head, tail = regex_to_nfa(regex)
        end = NFAState(outputs)
        for trans in tail:
            trans.tail = end
        return head, []

    if isinstance(regex, basestring):
        # string literal
        if len(regex) <= 1:
            # literal symbol or epsilon transition
            node = NFAState()
            trans = NFATransition(node, None, regex)
            node.transitions[regex].append(trans)
            return node, [trans]
        else:
            # implicit concatenation
            return regex_to_nfa(['cat'] + list(regex))
    else:
        # operator
        op, args = regex[0], regex[1:]
        if op == 'cat':
            # concatenation
            assert len(args) > 1
            nfas = [regex_to_nfa(a) for a in args]
            head, tail = nfas[0]
            for head1, tail1 in nfas[1:]:
                for trans in tail:
                    trans.tail = head1
                tail = tail1
            return head, tail
        elif op == 'alt':
            # alternation
            assert len(args) > 0
            nfas = [regex_to_nfa(a) for a in args]
            head = NFAState()
            tail = []
            for head1, tail1 in nfas:
                trans = NFATransition(head, head1, '')
                head.transitions[''].append(trans)
                tail.extend(tail1)
            return head, tail
        elif op == 'star':
            # Kleene closure
            assert len(args) == 1
            head, tail = regex_to_nfa(args[0])
            end = NFAState()
            for trans in tail:
                trans.tail = end
            skip_trans = NFATransition(head, end, '')
            head.transitions[''].append(skip_trans)
            loop_trans = NFATransition(end, head, '')
            end.transitions[''].append(loop_trans)
            out_trans = NFATransition(end, None, '')
            end.transitions[''].append(out_trans)
            return head, [out_trans]
        elif op == 'opt':
            assert len(args) == 1
            return regex_to_nfa(['alt', '', args[0]])
        elif op == 'plus':
            assert len(args) == 1
            return regex_to_nfa(['cat', args[0], ['star', args[0]]])
        elif op == 'range':
            syms = []
            for a in args:
                if isinstance(a, basestring):
                    syms.append(a)
                elif isinstance(a, list):
                    assert len(a) == 2
                    for i in xrange(ord(a[0]), ord(a[1])):
                        syms.append(chr(i))
                else:
                    raise ValueError('invalid argument to "range": %s' %\
                                     json.dumps(a))
            return regex_to_nfa(['alt'] + syms)
        elif op == 'class':
            assert len(args) == 1 and isinstance(args[0], basestring)
            klass = args[0]
            if klass == 'space':
                return regex_to_nfa(['range', ' ', '\n', '\r', '\t'])
            elif klass == 'digit':
                return regex_to_nfa(['range', ['0', '9']])
            elif klass == 'alpha':
                return regex_to_nfa(['range', ['a', 'z'], ['A', 'Z']])
            elif klass == 'alnum':
                return regex_to_nfa(['range', ['a', 'z'], ['A', 'Z'], 
                                              ['0', '9']])
            elif klass == 'name':
                return regex_to_nfa(['range', ['a', 'z'], ['A', 'Z'], 
                                              ['0', '9'], '_'])
            elif klass[0] == '!':
                syms = range(0x80)
                for a in klass[1:]:
                    syms.remove(ord(a))
                return regex_to_nfa(['alt'] + [chr(s) for s in syms])
            else:
                raise ValueError('unrecognized regex class %s' % json.dumps(klass))
        else:
            raise ValueError('unrecognized regex operator %s' % json.dumps(op))

def compile_lexerdef(path):
    with open(path) as f:
        lexerdef = json.load(f)

    lexer_head = NFAState()
    token_order = []
    for token_name, regex in lexerdef:
        token_head, _ = regex_to_nfa(regex, [token_name])
        trans = NFATransition(lexer_head, token_head, '')
        lexer_head.transitions[''].append(trans)
        token_order.append(token_name)

    # lexer_head is now the head of the full NFA for the lexer
    return lexer_head, token_order

#
# NFA -> DFA compiler
#

def epsilon_closure(nfa_states):
    stack = list(nfa_states)
    visited = set()
    while stack:
        state = stack.pop()
        if state in visited:
            continue
        visited.add(state)
        stack.extend(state.follow(''))
    return frozenset(visited)

def subset_output(nfa_states, token_order):
    all_outputs = []
    for nfa_state in nfa_states:
        all_outputs.extend(nfa_state.outputs)
    if len(all_outputs) == 0:
        return None
    return min(all_outputs, key=token_order.index)

def follow_all(nfa_states):
    trans_sets = defaultdict(list)
    for nfa_state in nfa_states:
        for symbol, succs in nfa_state.transitions.iteritems():
            trans_sets[symbol].extend(t.tail for t in succs if t.tail)
    for symbol, allsuccs in trans_sets.iteritems():
        if symbol != '':
            yield symbol, epsilon_closure(allsuccs)

def nfa_to_dfa(nfa_start, token_order):
    start = epsilon_closure([nfa_start])

    # build NFA state subset transition table
    subset_trans = defaultdict(dict)
    stack = [start]
    visited = set()
    while stack:
        state = stack.pop()
        if state in visited:
            continue
        visited.add(state)
        for symbol, succ in follow_all(state):
            subset_trans[state][symbol] = succ
            stack.append(succ)

    # TODO DFA minimization

    # number visited NFA subsets (fixing start and error at 1 and 0)
    subset_number = {
        frozenset([]): 0,
        start: 1
    }
    subset_number_next = 2
    for subset in visited:
        if subset in subset_number:
            continue
        subset_number[subset] = subset_number_next
        subset_number_next += 1

    # build DFA state transition table and output table
    output_table = [None for i in xrange(len(subset_number))]
    trans_table = [{} for i in xrange(len(subset_number))]
    for subset in visited:
        trans_table[subset_number[subset]] = {
            symbol: subset_number[succ]
            for symbol, succ in subset_trans.get(subset, {}).iteritems()
        }
        output_table[subset_number[subset]] = subset_output(subset, token_order)

    # build DFA input table
    used_symbols = list(set(s for row in trans_table for s in row.keys()))
    cols = {s: tuple(row.get(s) for row in trans_table) for s in used_symbols}
    cols_inv = defaultdict(list)
    for s, col in cols.iteritems():
        cols_inv[col].append(s)
    input_classes = [['\xff']] + list(cols_inv.values())

    input_table = {
            s: i 
        for i, icls in enumerate(input_classes) 
            for s in icls
    }

    # fix up transition table to use input table
    trans_table = [
        [row.get(icls[0], 0) for icls in input_classes]
        for row in trans_table
    ]

    # TODO reorder to reduce fill in trans_table matrix

    return input_table, trans_table, output_table

#
# DFA representation
#
# This lexer generator produces a DFA in the form of three tables, the input
# table, transition table, and output table. The input table is a map from
# strings to integers, the transition table is a 2D array of integers, and
# the output table is an array of strings and nulls.
#
# The state of the DFA starts at 1, and errors (or ends of tokens) are 
# indicated by a transition to state 0, which should trigger a reset to 1.
# On receiving an input symbol, the state is updated according to the
# following pseudocode:
#
# next_state = trans_table[curr_state][input_table[symbol]]
# if next_state == 0:
#     if output_table[curr_state] == None:
#         raise Error
#     yield output_table[curr_state] # emit token
#     next_state = 1
# curr_state = next_state
#
# (Note: a real lexer will require emitting more than just the token class)
#

def main(lexerdef_path, output_path=None):
    nfa_head, token_order = compile_lexerdef(lexerdef_path)
    dfa = nfa_to_dfa(nfa_head, token_order)

    output = {
        'input': dfa[0],
        'trans': dfa[1],
        'output': dfa[2]
    }

    json.dump(output, sys.stdout, separators=',:', sort_keys=True)

if __name__ == '__main__':
    main(*sys.argv[1:])
