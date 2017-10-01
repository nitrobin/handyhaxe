# handyhaxe
[![Build Status](https://travis-ci.org/nitrobin/handyhaxe.svg?branch=master)](https://travis-ci.org/nitrobin/handyhaxe)
[![Build status](https://ci.appveyor.com/api/projects/status/oqx3f9dxeg3hdpsw?svg=true)](https://ci.appveyor.com/project/nitrobin/handyhaxe)
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
    python handyhaxe.py --cwd samples --cmd haxe -x HelloWorld
    python handyhaxe.py --cwd samples --cmd haxe -main HelloWorld -neko out.n
    python handyhaxe.py --cwd samples --cmd neko out.n

## Make wrapper for specific haxe version

    python handyhaxe.py -haxe=latest -e=bash -o=haxe-latest-runner.sh --cmd haxe \"\$@\" \
        && chmod a+x haxe-latest-runner.sh 
    ./haxe-latest-runner.sh -version
    ./haxe-latest-runner.sh --cwd samples -x HelloWorld

## Customize environment 

Create python script with custom environment settings and preinstalled libraries

```python
# make-helloworld.py
import handyhaxe

handyhaxe.make_env("-haxe=3.4.3 -v", [
    "haxelib install format",
    "haxelib list",
    "haxe -neko HelloWorld.n -main HelloWorld",
    "neko HelloWorld.n"
])
```

## Notes
Must works on Windows/Linux/Mac. 
