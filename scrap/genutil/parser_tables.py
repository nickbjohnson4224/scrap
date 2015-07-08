import json
import sys
import os

from collections import defaultdict

def compile_parserdef(path):
    with open(path) as f:
        parserdef = json.load(f)

    # the rule "S -> a b c" is represented as (S, (a, b, c))
    rules = [
        (str(ntdef[0]), tuple(str(x) for x in ntdef[i]))
        for ntdef in parserdef
        for i in xrange(1, len(ntdef))
    ]

    # separate out nonterminals and terminals
    symbols = set(item for left, right in rules for item in (left,) + right)
    nonterminals = set(rule[0] for rule in rules)
    terminals = symbols - nonterminals
    start = rules[0][0]

    # style check (case rules for terminals/nonterminals)
    assert all(t.isupper() for t in terminals), 'found lowercase terminal'
    assert all(nt.islower() for nt in nonterminals), 'found uppercase nonterminal'

    # compute first and follow sets
    first = defaultdict(set)
    follow = defaultdict(set)
    nullable = set()

    for t in terminals:
        first[t] = set([t])

    dirty = True
    while dirty:
        dirty = False

        for left, right in rules:
            if all(y in nullable for y in right):
                if left not in nullable:
                    dirty = True
                nullable.add(left)
            for i in xrange(len(right)):
                if all(right[k] in nullable for k in xrange(i)):
                    if first[right[i]] - first[left]:
                        dirty = True
                    first[left] |= first[right[i]]
                if all(right[k] in nullable for k in xrange(i+1, len(right))):
                    if follow[left] - follow[right[i]]:
                        dirty = True
                    follow[right[i]] |= follow[left]
                for j in xrange(i+1, len(right)):
                    if all(right[k] in nullable for k in xrange(i+1, j)):
                        if first[right[j]] - follow[right[i]]:
                            dirty = True
                        follow[right[i]] |= first[right[j]]

    # sanity check (no nonterminals in first/follow)
    assert not any((first[s] | follow[s]) & nonterminals for s in symbols),\
        'nonterminal found in first or follow set'

    # create first sets for all right hand sides of rules
    for left, right in rules:
        for i, s in enumerate(right):
            first[right] |= first[right[0]]
            if s not in nullable:
                break

    for nt in nonterminals:
        print nt
        print first[nt]
        print follow[nt]

    table = {}
    for nt in nonterminals:
        for t in terminals:
            if t not in first[nt]:
                continue

            already_set = False
            for left, right in rules:
                if left != nt:
                    break
                if right and t in first[right]:
                    table[nt, t] = right
                    already_set = True
                elif not right and t in follow[nt]:
                    table[nt, t] = right
                    already_set = True
                else:
                    assert already_set, 'ambiguous rule for %r %r' % (nt, t)

    return table

def main(parserdef_path, output_path=None):
    ll1_table = compile_parserdef(parserdef_path)
    print ll1_table

if __name__ == '__main__':
    main(*sys.argv[1:])
