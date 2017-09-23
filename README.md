# handyhaxe
## What is it?

With this script you can quickly start development with haxe anywhere and anytime.
Just wrap you commands in handyhaxe.py and it will run in automatically configured environment with haxe and neko. You can easy switch between haxe versions with `--haxe-version` parameter. All files will be installed locally in `./.hh` directory and will not require host system modifictaion. HandyHaxe just download haxe and neko bianries to local directory `.hh`, configure environment variables (like $PATH) and execute your commands in this sandbox.

`python handyhaxe.py --cmd [COMMAND]`

## How to install?
* Install Python 2/3
* Download handyhaxe.py script to local directory.
* Open shell and execute `python handyhaxe.py`

## Sample usages:

    python handyhaxe.py --verbose --haxe-version=latest --cmd haxe -version    
    python handyhaxe.py --verbose --cmd haxe -version    
    python handyhaxe.py --cmd haxelib list
    python handyhaxe.py --cmd haxe -main HelloWorld -neko out.n
    python handyhaxe.py --cmd neko out.n

## Notes
Must works on Windows/Linux/Mac. 
