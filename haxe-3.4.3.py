import handyhaxe
import sys

handyhaxe.make_env("-haxe=3.4.3 -v",[
    "haxelib install format",
    "haxelib list ",
    ["haxe"] + sys.argv[1:]
])