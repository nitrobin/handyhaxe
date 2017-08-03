import argparse
import os.path
import urllib
import platform
import sys
import subprocess
import logging
import textwrap

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')


def splitArgs():
    if "--cmd" in sys.argv:
        i = sys.argv.index("--cmd")
        return (sys.argv[:i + 1], sys.argv[i + 1:])
    else:
        return (sys.argv, [])


def detectPlatform():
    p = platform.system()
    if p == "Linux":
        (arch, _) = platform.architecture()
        if arch == "64bit":
            return "linux64"
        else:
            return "linux32"
    elif p == "Darwin":
        return "osx"
    elif p == "Windows":
        return "win"
    return "win"


def parseArgs(argsEnv):
    parser = argparse.ArgumentParser(description='HandyHaxe: Instant environment for haxe development.',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=textwrap.dedent('''
Sample usages:\n
    python handyhaxe.py --verbose --haxe-version=latest --cmd haxe -version    
    python handyhaxe.py --verbose --cmd haxe -version    
    python handyhaxe.py --cmd haxelib list
    python handyhaxe.py --cmd haxe -main HelloWorld -neko out.n
    python handyhaxe.py --cmd neko out.n
    '''))
    parser.add_argument('command', metavar='CMD', nargs='*',
                        help='Command to execute in configured environment.')
    parser.add_argument('-haxe', '--haxe-version', help='Haxe version (x.x.x|latest)', default="3.4.2")
    parser.add_argument('--neko-version', help='Neko version (x.x.x|auto)', default="auto")
    parser.add_argument('--platform', default=detectPlatform(),
                        help="Platform (win|osx|linux64|linux32)")
    parser.add_argument('-i', '--install', action='store_true',
                        default=False, help='Install haxe local')
    parser.add_argument('--install-path', default=".hh",
                        help='Path to store local files')
    parser.add_argument('--cmd', default=False,
                        action="store_true", help='Run cmd')
    parser.add_argument('-v', '--verbose', default=False,
                        action="store_true", help='Verbose mode')

    if len(sys.argv) < 2:
        parser.print_help()

    return parser.parse_args(argsEnv)


def installPackage(package, e):
    url = package.url
    if not os.path.exists(e.install_path):
        os.makedirs(e.install_path)
    fileName = os.path.normpath(e.install_path + "/" + package.fileName)
    dirName = os.path.normpath(e.install_path + "/" + package. dirName)
    fileExist = os.path.isfile(fileName)
    logging.info("{0} -> {1} - [{2}]".format(url, fileName,
                                             "CACHED" if fileExist else "DOWNLOAD"))
    if not fileExist:
        if sys.version_info[0] < 3:
            import urllib
            urllib.urlretrieve(url, fileName)
        else:
            import urllib.request
            urllib.request.urlretrieve(url, fileName)

    if not os.path.exists(dirName):
        logging.debug("Exracting to {}..".format(dirName))
        os.makedirs(dirName)
        if fileName.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(fileName, "r") as a:
                a.extractall(dirName)
        if fileName.endswith(".tar.gz"):
            import tarfile
            with tarfile.open(fileName) as a:
                a.extractall(dirName)
        # Strip empty dir level
        ld = os.listdir(dirName)
        if len(ld) == 1:
            tmpDir = dirName + ".tmp"
            os.rename(dirName, tmpDir)
            os.rename(os.path.normpath(tmpDir + "/" + ld[0]), dirName)
            os.rmdir(tmpDir)
    # Collect Paths
    for packagePath in package.exportPaths:
        p = os.path.abspath(os.path.normpath(dirName + "/" + packagePath))
        e.path.append(p)
    # Collect variables
    for (varName, p) in package.exportVars.items():
        ap = os.path.abspath(os.path.normpath(dirName + "/" + p))
        e.env[varName] = ap
        if not os.path.exists(ap):
            os.makedirs(ap)


class Package():
    def __init__(self, name, url, fileName, dirName, exportVars, exportPaths):
        self.name = name
        self.url = url
        self.fileName = fileName
        self.dirName = dirName
        self.exportVars = exportVars
        self.exportPaths = exportPaths

    def replace(self, params):
        if params != None:
            self.url = self.url.format(**params)
            self.fileName = self.fileName.format(**params)
            self.dirName = self.dirName.format(**params)


class EvnExport:
    def __init__(self, install_path):
        self.env = {}
        self.path = []
        self.install_path = install_path

    def createFinalEnv(self, baseEnv={}):
        p = self.path
        if "PATH" in baseEnv:
            p = p + [baseEnv["PATH"]]
        baseEnv["PATH"] = os.pathsep.join(p)
        for (k, v) in self.env.items():
            baseEnv[k] = v
        return baseEnv


class App:
    installed = False
    packages = []

    def __init__(self, packages):
        self.packages = packages
        (argsEnv, argsCmd) = splitArgs()
        self.argsEnv = argsEnv
        self.argsCmd = argsCmd
        self.args = parseArgs(self.argsEnv)
        if not self.args.verbose:
            logging.disable(logging.INFO)
        logging.info ("Python version: {}".format(sys.version_info))
        logging.info("ARGS: {}".format(self.args))

        self.e = EvnExport(self.args.install_path)
        #self.e = EvnExport({}, args.install_path)

        if self.args.neko_version == "auto":
            v = self.args.haxe_version
            if v[:1] in ["2"]:
                self.args.neko_version = "1.8.2"
            elif v[:3] in ["3.0", "3.1", "3.2"]:
                self.args.neko_version = "2.0.0"
            else:
                self.args.neko_version = "2.1.0"
        
        def filterPackages(toInstall):
            self.packages = [p for p in self.packages if p.name in toInstall]
        if self.args.haxe_version =="latest":
            filterPackages(["haxe-latest", "neko"])
        else:
            filterPackages(["haxe", "neko"])

        platform2 = self.args.platform
        if platform2 == "win":
            platform2 = "windows"
        elif platform2 == "osx":
            platform2 = "mac"

        self.params = {
            "haxe_version": self.args.haxe_version,
            "neko_version": self.args.neko_version,
            "platform": self.args.platform,
            "platform2": platform2 ,
            "extension": "zip" if self.args.platform == "win" else "tar.gz"
        }

    def stepInstall(self):
        if self.installed:
            return
        self.installed = True
        for p in self.packages:
            p.replace(self.params)
            installPackage(p, self.e)

    def stepCommand(self):
        self.stepInstall()
        shortEnv = "\n".join(
            map(lambda i: "    {} : {}".format(*i), self.e.createFinalEnv().items()))
        logging.info("Packages ENV:\n{}".format(shortEnv))
        logging.info("CMD: {}".format(self.argsCmd))
        fullEnv = self.e.createFinalEnv(os.environ.copy())
        os.environ["PATH"] = fullEnv["PATH"]
        p = subprocess.Popen(self.argsCmd, env=fullEnv, stdin=sys.stdin,
                             stdout=sys.stdout, stderr=sys.stderr)
        p.wait()
        sys.exit(p.returncode)

    def run(self):
        if self.args.install:
            self.stepInstall()

        if self.args.cmd:
            self.stepCommand()

#-----------------------------------------------------------------------------


packages = []

# Neko
packages.append(
    Package(
        "neko",
        "http://nekovm.org/media/neko-{neko_version}-{platform}.{extension}",
        "neko-{neko_version}-{platform}.{extension}",
        "neko-{neko_version}-{platform}",
        {
            "NEKO_PATH": ".",
            "LD_LIBRARY_PATH": "."
        },
        ["."]
    )
)

# Haxe
packages.append(
    Package(
        "haxe",
        "https://github.com/HaxeFoundation/haxe/releases/download/{haxe_version}/haxe-{haxe_version}-{platform}.{extension}",
        "haxe-{haxe_version}-{platform}.{extension}",
        "haxe-{haxe_version}-{platform}",
        {
            "HAXE_PATH": ".",
            "HAXE_STD_PATH": "./std",
            "HAXELIB_PATH": "../haxelib"
        },
        ["."]
    )
)

# Haxe Nightly Builds 
packages.append(
    Package(
        "haxe-latest",
        "http://hxbuilds.s3-website-us-east-1.amazonaws.com/builds/haxe/{platform2}/haxe_latest.{extension}",
        "haxe-latest-{platform2}.{extension}",
        "haxe-latest-{platform2}",
        {
            "HAXE_PATH": ".",
            "HAXE_STD_PATH": "./std",
            "HAXELIB_PATH": "../haxelib"
        },
        ["."]
    )
)

#-----------------------------------------------------------------------------

App(packages).run()
