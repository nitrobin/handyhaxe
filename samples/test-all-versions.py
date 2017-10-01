#!/usr/bin/env python
#https://stackoverflow.com/questions/11536764/how-to-fix-attempted-relative-import-in-non-package-even-with-init-py
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import handyhaxe

def test(version):
    handyhaxe.make_env("-haxe=" + version,[
        "haxelib install format",
        "haxelib list ",
        "haxe -x HelloWorld"
    ])

test("latest")
test("3.4.3")
test("3.2.1")
