#https://stackoverflow.com/questions/11536764/how-to-fix-attempted-relative-import-in-non-package-even-with-init-py
import handyhaxe
import sys

handyhaxe.make_env("-haxe=3.4.3 -v",[
    "haxelib install format",
    "haxelib list ",
    ["haxe"] + sys.argv[1:]
])