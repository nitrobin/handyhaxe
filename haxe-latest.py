import handyhaxe
import sys

handyhaxe.make_env("-haxe=latest -v",[
    "haxelib install format",
    "haxelib list ",
    ["haxe"] + sys.argv[1:]
])