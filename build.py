#/usr/bin/env python2

import sys
import os

class ScriptRule(object):

    def __init__(self, interp, script, targets, sources):
        self._interp = interp
        self._script = script
        self._targets = targets
        self._sources = sources
        self.deps = (script,) + tuple(sources)
        self.targets = tuple(targets)

    def run(self):
        os.system('%s %s', self._interp, self._script

lexergen = lambda target, source:
    ScriptRule('python', 'src/lexergen.py', [target], [source]

rules = [
    lexergen('build/lexertab.json', 'src/lexerdef.json')
]

def main():
    

if __name__ == '__main__':
    main(*sys.argv[1:])
