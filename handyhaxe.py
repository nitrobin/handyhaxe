import argparse
import os.path
import urllib
import platform
import sys
import subprocess
import logging
import textwrap
import zipfile
import tarfile

#-----------------------------------------------------------------------------

class Package():
    def __init__(self):
        self.name = ""
        self.url = ""
        self.packageFile = ""
        self.packageDir = ""
        self.exportVars = {}
        self.exportPaths = []


class EnvironmentExport:
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


def getPackageInfo(packageName, version, platformName):
    packages = {
        "neko": {
            "urls": {
                "{version}": {
                    "win": "http://nekovm.org/media/neko-{version}-win.zip",
                    "osx": "http://nekovm.org/media/neko-{version}-osx64.tar.gz",
                    "linux": "http://nekovm.org/media/neko-{version}-linux64.tar.gz"
                }
            },
            "exportVariables": {
                "NEKO_PATH": ".",
                "LD_LIBRARY_PATH": ".",
                "DYLD_FALLBACK_LIBRARY_PATH": ".",
                "DYLD_LIBRARY_PATH":"."
            },
            "exportPath": ["."]
        },
        "haxe": {
            "urls": {
                "{version}": {
                    "win":   "https://github.com/HaxeFoundation/haxe/releases/download/{version}/haxe-{version}-win.zip",
                    "osx":   "https://github.com/HaxeFoundation/haxe/releases/download/{version}/haxe-{version}-osx.tar.gz",
                    "linux": "https://github.com/HaxeFoundation/haxe/releases/download/{version}/haxe-{version}-linux64.tar.gz"
                },
                "latest": {
                    "win":   "http://hxbuilds.s3-website-us-east-1.amazonaws.com/builds/haxe/windows/haxe_latest.zip#/haxe-latest-win.zip",
                    "osx":   "http://hxbuilds.s3-website-us-east-1.amazonaws.com/builds/haxe/mac/haxe_latest.tar.gz#/haxe-latest-osx.tar.gz",
                    "linux": "http://hxbuilds.s3-website-us-east-1.amazonaws.com/builds/haxe/linux64/haxe_latest.tar.gz#/haxe-latest-linux64.tar.gz"
                }
            },
            "exportVariables": {
                "HAXE_PATH": ".",
                "HAXE_STD_PATH": "./std",
                "HAXELIB_PATH": "../haxelib"
            },
            "exportPath": ["."]
        },
        "vscode": {
            "urls": {
                "stable": {
                    "win":   "https://go.microsoft.com/fwlink/?Linkid=850641#/vscode-stable-win.zip",
                    "osx":   "https://go.microsoft.com/fwlink/?LinkID=620882#/vscode-stable-osx.zip",
                    "linux": "https://go.microsoft.com/fwlink/?LinkID=620884#/vscode-stable-linux64.tar.gz",
                },
                "insider": {
                    "win":   "https://go.microsoft.com/fwlink/?Linkid=850640#/vscode-insider-win.zip",
                    "osx":   "https://go.microsoft.com/fwlink/?LinkId=723966#/vscode-insider-osx.zip",
                    "linux": "https://go.microsoft.com/fwlink/?LinkId=723968#/vscode-insider-linux64.tar.gz"
                }
            },
            "exportVariables": {
            },
            "exportPath": ["."]
        },
        "hashlink": {
            "urls": {
                "{version}": {
                    "win":   "https://github.com/HaxeFoundation/hashlink/releases/download/{version}/hl-{version}-win32.zip",
                    "osx":   "https://github.com/HaxeFoundation/hashlink/releases/download/{version}/hl-{version}-osx.zip",
                    #"linux": "https://github.com/HaxeFoundation/hashlink/releases/download/{version}/hl-{version}-linux64.tar.gz"
                }
            },
            "exportVariables": {
                "LD_LIBRARY_PATH": "."
            },
            "exportPath": ["."]
        }
    }
    package = Package()
    package.name = packageName

    packageInfo = packages[packageName]
    package.exportVars = packageInfo["exportVariables"]
    package.exportPaths = packageInfo["exportPath"]

    packageUrls = packageInfo["urls"]

    if packageUrls != None:
        versionUrls = packageUrls.get(version)
        if versionUrls == None and packageUrls["{version}"] != None:
            package.url = packageUrls["{version}"][platformName].format(version=version)
        else:
            package.url = versionUrls[platformName]

    if package.url != None:
        package.packageFile = package.url.split("/")[-1]
        package.packageDir = package.packageFile.replace(".zip", "").replace(".tar.gz", "")
    else:
        return None
    package.url = package.url.split("#")[0]
    return package

#-----------------------------------------------------------------------------

def urlretrieve(url, packageFile):
    if sys.version_info[0] < 3:
        import urllib
        urllib.urlretrieve(url, packageFile)
    else:
        import urllib.request
        urllib.request.urlretrieve(url, packageFile)


def extractall(packageFile, packageDir):
    os.makedirs(packageDir)
    if packageFile.endswith(".zip"):
        with zipfile.ZipFile(packageFile, "r") as a:
            a.extractall(packageDir)
    if packageFile.endswith(".tar.gz"):
        with tarfile.open(packageFile) as a:
            a.extractall(packageDir)
    # Strip empty dir level
    ld = os.listdir(packageDir)
    if len(ld) == 1:
        tmpDir = packageDir + ".tmp"
        os.rename(packageDir, tmpDir)
        os.rename(os.path.normpath(tmpDir + "/" + ld[0]), packageDir)
        os.rmdir(tmpDir)

#-----------------------------------------------------------------------------



class App:
    installed = False
    packages = []

    def __init__(self, appArgv=None, commands = []):
        # platform
        (arch, _) = platform.architecture()
        self.is_64bit = (arch == "64bit")
        platforms = {"Linux": "linux", "Darwin": "osx", "Windows": "win"}
        self.platformName = platforms[platform.system()]
        self.is_linux = self.platformName == "linux"
        self.is_win = self.platformName == "win"
        self.is_osx = self.platformName == "osx"

        if isinstance(appArgv, str):
            appArgv = appArgv.split(" ")

        # split args
        appArgv = appArgv if appArgv != None else sys.argv
        self.appArgv = appArgv
        self.commands = commands
        if "--cmd" in self.appArgv:
            i = self.appArgv.index("--cmd")
            self.appArgv = appArgv[:i]
            self.commands = self.commands + [appArgv[i + 1:]]
            
        # parse
        self.args = self.parseArgs(self.appArgv, self.platformName)
        # debug info
        if not self.args.verbose:
            logging.disable(logging.INFO)
        logging.info("Python version: {}".format(platform.python_version()))
        logging.info("ARGS: {}".format(self.args))

        self.e = EnvironmentExport(self.args.install_path)

        if self.args.neko_version == "auto":
            v = self.args.haxe_version
            if v[:1] in ["2"]:
                self.args.neko_version = "1.8.2"
            elif v[:3] in ["3.0", "3.1", "3.2"]:
                self.args.neko_version = "2.0.0"
            else:
                self.args.neko_version = "2.1.0"
        # add packages
        self.packages = [
            getPackageInfo("haxe", self.args.haxe_version, self.args.platform),
            getPackageInfo("neko", self.args.neko_version, self.args.platform)
        ]
        if self.args.vscode_version != None:
            self.packages.append(
                getPackageInfo("vscode", self.args.vscode_version, self.args.platform)
            )
        if self.args.hashlink_version != None:
            self.packages.append(
                getPackageInfo("hashlink", self.args.hashlink_version, self.args.platform)
            )


    def parseArgs(self, appArgv, defaultPlatform):
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
        parser.add_argument('-haxe', '--haxe-version',
                            help='Haxe version (x.x.x|latest)', default="3.4.3")
        parser.add_argument(
            '--neko-version', help='Neko version (x.x.x|auto)', default="auto")
        parser.add_argument('-vscode', '--vscode-version',
                            help='VSCode version (stable|insider)', default=None)
        parser.add_argument('-hl', '--hashlink-version',
                            help='Hashlink version', default=None)
        parser.add_argument('--platform', default=defaultPlatform,
                            help="Platform (win|osx|linux) 64 bit only.")
        parser.add_argument('-i', '--install', action='store_true',
                            default=False, help='Install haxe local')
        parser.add_argument('--install-path', default=".hh",
                            help='Path to store local files')
        parser.add_argument('-o', '--output', default=None,
                            help='Output file name')
        parser.add_argument('-e', '--export', default=None,
                            help='Print environment variables script to stdout or to output file. Format (cmd|bash)')
        parser.add_argument('--cmd', default=False,
                            action="store_true", help='Run cmd')
        parser.add_argument('-v', '--verbose', default=False,
                            action="store_true", help='Verbose mode')
        parser.add_argument('--cwd', default=None, help='Change working directory')

        if len(appArgv) < 2:
            parser.print_help()

        return parser.parse_args(appArgv)


    def run(self):
        if self.args.export != None:
            self.stepInstall()
            self.stepExport()
            sys.exit(0)

        if self.args.install:
            self.stepInstall()

        if len(self.commands) > 0:
            self.stepCommand()

    def stepCommand(self):
        self.stepInstall()
        shortEnv = "\n".join(map(lambda i: '  {}:"{}"'.format(*i), self.e.createFinalEnv().items()))
        logging.info("Environment variables:\n{}".format(shortEnv))

        fullEnv = self.e.createFinalEnv(os.environ.copy())
        os.environ["PATH"] = fullEnv["PATH"]
        logging.info("PATH:\n{}".format(os.environ["PATH"]))

        for command in self.commands:
            if callable(command):
                command = command(self)
                if command is None:
                    continue
            #if isinstance(command, str):
            #   command = command.split(" ")
            logging.info("command: {}".format(command))
            p = subprocess.Popen(command, env=fullEnv, stdin=sys.stdin, shell=isinstance(command, str),
                                 stdout=sys.stdout, stderr=sys.stderr,cwd=self.args.cwd)
            p.wait()
            if p.returncode != 0:
                sys.exit(p.returncode)


    def stepExport(self):
        format = self.args.export
        lines = []
        PATH_VAR = "${PATH%}"
        KV_FORMAT = '{}:"{}"'
        if format == "cmd":
            PATH_VAR = "%PATH%"
            KV_FORMAT = 'set {}="{}"'
        if format == "bash":
            PATH_VAR = "${PATH}"
            KV_FORMAT = 'export {}="{}"'
        for (k, v) in self.e.createFinalEnv().items():
            if k == "PATH":
                v = os.pathsep.join([v, PATH_VAR])
            lines.append(KV_FORMAT.format(k, repr(v)[1:-1]))
            
        for cmd in self.commands:
            lines.append(" ".join(cmd))
        envs = '\n'.join(lines) + "\n"
        output = self.args.output
        if output == None:
             print(envs)
        else:
            output = os.path.abspath(os.path.normpath(output))            
            if not os.path.exists(os.path.dirname(output)):
                os.makedirs(os.path.dirname(output))
            with open(output, 'w') as out:
                out.write(envs)


    def stepInstall(self):
        if self.installed:
            return
        self.installed = True
        for p in self.packages:
            self.installPackage(p)

    def installPackage(self, package):
        e = self.e
        url = package.url
        if not os.path.exists(e.install_path):
            os.makedirs(e.install_path)
        packageFile = os.path.normpath(e.install_path + "/" + package.packageFile)
        packageDir = os.path.normpath(e.install_path + "/" + package.packageDir)
        fileExist = os.path.isfile(packageFile)
        logging.info("{0} -> {1} - [{2}]".format(url, packageFile, "EXIST" if fileExist else "DOWNLOAD"))
        if not fileExist:
            af = os.path.abspath(os.path.normpath(packageFile))            
            if not os.path.exists(os.path.dirname(af)):
                os.makedirs(os.path.dirname(af))
            urlretrieve(url, packageFile)

        if not os.path.exists(packageDir):
            logging.debug("Exracting to {}..".format(packageDir))
            extractall(packageFile, packageDir)

        # Collect Paths
        for packagePath in package.exportPaths:
            p = os.path.abspath(os.path.normpath(
                packageDir + "/" + packagePath))
            e.path.append(p)
        # Collect variables
        for (varName, p) in package.exportVars.items():
            ap = os.path.abspath(os.path.normpath(packageDir + "/" + p))
            e.env[varName] = ap
            if not os.path.exists(ap):
                os.makedirs(ap)

#-----------------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def make_env(appArgv, commands):
    if isinstance(appArgv, str):
        appArgv = appArgv.split(" ")
    appArgv = ["handyhaxe.py"] + appArgv
    App(appArgv, commands).run()

if __name__ == "__main__":
    App().run()
