# coding=iso-8859-15
import json
import os
from subprocess import call, check_call
import subprocess
import sys
import traceback
import winreg
import pip
import numpy
import inspect
import jedi
import flake8
import platform

__version__ = "1.0.0"


# -------------------------------------------
class Main:
    def __init__(self):
        """ """
        # private members
        self.__settingsFileName = "setup_settings.txt"
        self.__currentDir = os.path.realpath(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))

        # public members
        self.itomSourcePath = self.__clearPath("..\\sources\\itom")
        self.itomBuildPath = self.__clearPath("..\\build\\itom")
        self.pluginSourcePath = self.__clearPath("..\\sources\\plugins")
        self.pluginBuildPath = self.__clearPath("..\\build\\plugins")
        self.designerPluginsSourcePath = self.__clearPath("..\\sources\\designerplugins")
        self.designerPluginsBuildPath = self.__clearPath("..\\build\\designerplugins")
        self.config = {"git_path": None, "build_with_pcl": None, "cmake_dir": None}
        self.status = {
            "pipUpgraded": False,
            "numpyInstalled": False,
            "jediInstalled": False,
            "pyflakesInstalled": False,
            "numpyVersionHigher": False,
            "itomGitCloned": False,
            "pluginGitCloned": False,
            "designerPluginGitCloned": False,
            "itomCMake": False,
            "pluginCMake": False,
            "designerPluginCMake": False,
            "itomCompiled": False,
            "pluginsCompiled": False,
            "designerpluginsCompiled": False,
        }

        # load config and start user input
        self.loadConfig()
        self.userInput()
        self.saveConfig()

        return

    def __clearPath(self, path: str) -> str:
        """clear path and replace slashs

        Args:
            path (str): Input path string

        Returns:
            str: clear path string
        """
        currentDir = os.path.realpath(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
        if os.path.isabs(path):
            return os.path.realpath(path)
        else:
            currentDir = os.path.realpath(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
        return os.path.realpath(os.path.join(currentDir, path)).replace("\\", "/")

    def __mkdir_recursive(self, path: str):
        """Move directories recursive

        Args:
            path (str): Input path
        """
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self.__mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

        return

    def loadConfig(self):
        """Load a save config to the member self.config"""
        if os.path.exists(self.__settingsFileName):
            with open(self.__settingsFileName, "r") as fp:
                temp = json.load(fp)
                self.config.update(temp)

        return

    def saveConfig(self):
        """Saves the self.config content to hard drive"""
        with open(self.__settingsFileName, "w") as fp:
            json.dump(self.config, fp, indent=4)

    def getStatus(self):
        """Get the status of the all in one build steps"""
        # status of git clone
        if os.path.exists(os.path.join(self.itomSourcePath, ".git")):
            self.status["itomGitCloned"] = True
        if os.path.exists(os.path.join(self.pluginSourcePath, ".git")):
            self.status["pluginGitCloned"] = True
        if os.path.exists(os.path.join(self.designerPluginsSourcePath, ".git")):
            self.status["designerPluginGitCloned"] = True

        # status of VS build
        if os.path.exists(os.path.join(self.itomBuildPath, "ALL_BUILD.vcxproj")):
            self.status["itomCMake"] = True
        if os.path.exists(os.path.join(self.itomBuildPath, "qitom.exe")) and os.path.exists(
            os.path.join(self.itomBuildPath, "qitomd.exe")
        ):
            self.status["itomCompiled"] = True
        if os.path.exists(os.path.join(self.pluginBuildPath, "ALL_BUILD.vcxproj")):
            self.status["pluginCMake"] = True
        if os.path.exists(os.path.join(self.designerPluginsBuildPath, "ALL_BUILD.vcxproj")):
            self.status["designerPluginCMake"] = True
        if os.path.isdir(self.itomBuildPath + "/plugins/" + "BasicFilters"):
            self.status["pluginsCompiled"] = True
        if os.path.isdir(self.itomBuildPath + "/designer/" + "itom1DQwtPlot"):
            self.status["designerpluginsCompiled"] = True
        return

    def askForGit(self):
        """ask user to git path input

        Raises:
            RuntimeError: Runtime error if git path does not exists in env
        """
        git = self.config["git_path"]

        if git is None or not os.path.exists(git):
            if git is None:
                print("No git path is given. Try to find the path to git.exe in the registry...")
            else:
                print(
                    "The git path",
                    git,
                    "does not exist. Retry to find the path to git.exe in the registry...",
                )

            regOptions = [
                [winreg.HKEY_CURRENT_USER, r"Software\Git-Cheetah", "PathToMsys"],
                [winreg.HKEY_LOCAL_MACHINE, r"Software\Git-Cheetah", "PathToMsys"],
                [winreg.HKEY_CURRENT_USER, r"Software\GitForWindows", "InstallPath"],
                [winreg.HKEY_LOCAL_MACHINE, r"Software\GitForWindows", "InstallPath"],
            ]

            path = None
            for [master, directory, key] in regOptions:
                try:
                    item = winreg.OpenKey(master, directory)
                    path = os.path.join(
                        os.path.abspath(winreg.QueryValueEx(item, key)[0]),
                        "bin",
                        "git.exe",
                    )
                    winreg.CloseKey(item)
                    if path != "":
                        break
                    else:
                        path = None
                except Exception:
                    pass

            if not path is None:
                print("found the path", path, "in the registry.")
                inp = input("Is this correct (y,n)?")
                if inp == "y":
                    git = path
                else:
                    git = input("Absolute path of git.exe (e.g. C:\\\\Program Files\\\\Git\\\\bin\\\\git.exe)?")
            else:
                print("Absolute path to git.exe could not be found automatically.")
                git = input("Absolute path of git.exe (e.g. C:\\\\Program Files\\\\Git\\\\bin\\\\git.exe)?")

            if not os.path.exists(git):
                raise RuntimeError("git path '%s' does not exist" % git)

            self.config["git_path"] = git
            test = "%(git)s" % {"git": git}  # only in order to raise an Exception and avoid to save invalid names
            self.saveConfig()

            return

    def askForPCL(self):
        """ask if itom is build with PCL

        Raises:
            RuntimeError: Runtime error if user input is not 'y' or 'n'
        """
        if (
            not "build_with_pcl" in self.config
            or self.config["build_with_pcl"] is None
            or (self.config["build_with_pcl"] != "TRUE" and self.config["build_with_pcl"] != "FALSE")
        ):
            inp = input("Build itom with PCL support (y,n)?")
            if inp == "y" or inp == "Y":
                self.config["build_with_pcl"] = "TRUE"
            elif inp == "n" or inp == "N":
                self.config["build_with_pcl"] = "FALSE"
            else:
                raise RuntimeError("wrong input for question if itom should be build with PCL support")

            self.saveConfig()
        return

    def cloneGit(self):
        """
        clone the itom, plugins and designerplugins repositories from https://github.com/itom-project
        to the ../sources directory.
        """
        git = self.config["git_path"]
        if git is None:
            self.askForGit()
            self.loadConfig()
            git = self.config["git_path"]

        cmd = "%(git_dir)s clone %(url)s %(directory)s"
        if not os.path.exists(self.__currentDir + "\\..\\sources"):
            os.mkdir(self.__currentDir + "\\..\\sources")

        # clone itom
        if os.path.exists(self.__currentDir + "..\\sources\\itom"):
            raise RuntimeError("The folder '../sources/itom' does already exist. Delete it first.")
        cmd_ = cmd % {
            "git_dir": git,
            "url": "https://github.com/itom-project/itom.git",
            "directory": self.__currentDir + "\\..\\sources\\itom",
        }
        call(cmd_)

        # clone plugins
        if os.path.exists(self.__currentDir + "..\\sources\\plugins"):
            raise RuntimeError("The folder '../sources/plugins' does already exist. Delete it first.")
        cmd_ = cmd % {
            "git_dir": git,
            "url": "https://github.com/itom-project/plugins.git",
            "directory": self.__currentDir + "\\..\\sources\\plugins",
        }
        call(cmd_)

        # clone designer plugins
        if os.path.exists(self.__currentDir + "..\\sources\\designerplugins"):
            raise RuntimeError("The folder '../sources/designerplugins' does already exist. Delete it first.")
        cmd_ = cmd % {
            "git_dir": git,
            "url": "https://github.com/itom-project/designerPlugins.git",
            "directory": self.__currentDir + "\\..\\sources\\designerplugins",
        }
        call(cmd_)
        return

    def runCMakeItom(self):
        """run cmake for itom project"""
        if not os.path.exists(self.itomBuildPath):
            self.__mkdir_recursive(self.itomBuildPath)

        return self.configureItom(self.itomSourcePath, self.itomBuildPath, self.generateCMakeDict())

    def runCMakePlugins(self) -> int:
        """run cmake for plugins and designerplugins

        Returns:
            int: Result of executing CMake generation
        """
        itom_sdk_dir = self.__clearPath(os.path.abspath(os.path.join(self.itomBuildPath, "SDK")))

        print("Configure DESIGNERPLUGINS...")
        if not os.path.exists(self.designerPluginsBuildPath):
            self.__mkdir_recursive(self.designerPluginsBuildPath)
        result2 = self.configurePlugins(
            self.designerPluginsSourcePath, self.designerPluginsBuildPath, self.generateCMakeDict(), itom_sdk_dir
        )

        print("Configure PLUGINS...")
        if not os.path.exists(self.pluginBuildPath):
            self.__mkdir_recursive(self.pluginBuildPath)
        result1 = self.configurePlugins(
            self.pluginSourcePath, self.pluginBuildPath, self.generateCMakeDict(), itom_sdk_dir
        )

    def configurePlugins(self, source_dir: str, build_dir: str, cmake_dict: dict, itom_sdk_dir: str) -> int:
        """Configure plugin solution

        Args:
            source_dir (str): Git repo source dir
            build_dir (str): build dir
            cmake_dict (dict): CMake config as dict
            itom_sdk_dir (str): itom SDK dir

        Returns:
            int: Result of executing CMake generation
        """
        configureCommandTemplate = (
            '%(cmake_executable)s -G "%(generator)s" -A "%(arch)s" -DITOM_LANGUAGES:STRING=%(itom_languages)s '
            + '-DOpenCV_DIR:PATH="%(opencv_dir)s" -DBUILD_WITH_PCL:BOOL=%(build_with_pcl)s -DBUILD_QTVERSION:STRING=%(build_qtversion)s '
            + '-DQT_QMAKE_EXECUTABLE:FILEPATH="%(qmake_dir)s" -DBUILD_TARGET64:BOOL=TRUE '
            + '-DCONSIDER_GIT_SVN:BOOL=FALSE -DPREFER_GIT:BOOL=TRUE "%(source_dir)s" '
            + '-DQt_Prefix_DIR:PATH="%(qt_prefix_dir)s" -DITOM_SDK:PATH="%(itom_sdk_dir)s" '
            + '-DITOM_SDK_DIR:PATH="%(itom_sdk_dir)s" -DPCL_DIR:PATH="%(pcl_dir)s" '
            + '-DBoost_USE_STATIC_LIBS:BOOL=ON -DVTK_DIR:PATH="%(vtk_dir)s" '
            + '-DBoost_INCLUDE_DIR:PATH="%(boost_include_dir)s" -DEIGEN_INCLUDE_DIR:PATH="%(eigen_include_dir)s" '
            + '-DFLANN_INCLUDE_DIRS:PATH="%(flann_include_dir)s" -DFLANN_INCLUDE_DIR:PATH="%(flann_include_dir)s" -DFLANN_LIBRARY:FILEPATH="%(flann_library)s" -DFLANN_LIBRARY_DEBUG:FILEPATH="%(flann_library_debug)s" '
            + '-DQHULL_INCLUDE_DIRS:PATH="%(qhull_include_dir)s" -DQHULL_LIBRARY:FILEPATH="%(qhull_library_dir)s" -DQHULL_LIBRARY_DEBUG:FILEPATH="%(qhull_library_dir_debug)s" '
            + '-DPCL_FLANN_REQUIRED_TYPE:STRING=STATIC -DFLANN_ROOT:PATH="%(flann_root)s" '
        )

        d = cmake_dict.copy()
        d.update({"source_dir": source_dir, "build_dir": build_dir, "itom_sdk_dir": itom_sdk_dir})

        fullConfigureCommand = configureCommandTemplate % d
        print(fullConfigureCommand)
        print("...")

        result = 1
        filePath = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        os.chdir(build_dir)
        
        success = False
        
        try:
            result = check_call(fullConfigureCommand, shell=False)
            success = True
        except subprocess.CalledProcessError:
            # for unknown reasons, CMake has to be run twice for a successful configuration.
            success = True # do not retry
        except Exception as ex:
            print("ERROR:", ex)
            print("Exception in user code:")
            print("-" * 60)
            traceback.print_exc(file=sys.stdout)
            print("-" * 60)
        
        if not success:
            # 2nd try
            try:
                result = check_call(fullConfigureCommand, shell=False)
                success = True
            except Exception as ex:
                print("ERROR:", ex)
                print("Exception in user code:")
                print("-" * 60)
                traceback.print_exc(file=sys.stdout)
                print("-" * 60)

        os.chdir(filePath)

        if result != 0:
            print("########################")
            print("ERROR CONFIGURING CMAKE")
            print("CMake Gui is opened. Try to generate the project and close the cmake gui again.")
            cmake_gui = self.__clearPath(os.path.join(os.path.dirname(cmake_dict["cmake_executable"]), "cmake-gui.exe"))
            call("%(cmake_gui_executable)s %(build_dir)s" % d)

        return result

    def configureItom(self, source_dir: str, build_dir: str, cmake_dict: dict) -> int:
        """Configure itom solution

        Args:
            source_dir (str): Git repo source dir
            build_dir (str): build dir
            cmake_dict (dict): CMake config as dict

        Returns:
            int: Result of executing CMake generation
        """
        configureCommandTemplate = (
            '%(cmake_executable)s -G "%(generator)s" -A "%(arch)s" -DITOM_LANGUAGES:STRING=%(itom_languages)s -DOpenCV_DIR:PATH="%(opencv_dir)s" -DBUILD_WITH_PCL:BOOL=%(build_with_pcl)s -DBUILD_QTVERSION:STRING=%(build_qtversion)s '
            + '-DQT_QMAKE_EXECUTABLE:FILEPATH="%(qmake_dir)s" -DBUILD_TARGET64:BOOL=TRUE -DPython_ROOT_DIR:FILEPATH="%(python_root_dir)s" '
            + '-DCONSIDER_GIT_SVN:BOOL=TRUE -DPREFER_GIT:BOOL=TRUE "%(source_dir)s" '
            + '-DQt_Prefix_DIR:PATH="%(qt_prefix_dir)s" -DPCL_DIR:PATH="%(pcl_dir)s" -DBoost_USE_STATIC_LIBS:BOOL=ON -DVTK_DIR:PATH="%(vtk_dir)s" '
            + '-DBoost_INCLUDE_DIR:PATH="%(boost_include_dir)s" -DEIGEN_INCLUDE_DIR:PATH="%(eigen_include_dir)s" '
            + '-DPCL_FLANN_REQUIRED_TYPE:STRING=STATIC -DFLANN_ROOT:PATH="%(flann_root)s" '
        )

        d = cmake_dict.copy()
        d.update({"source_dir": source_dir, "build_dir": build_dir})

        fullConfigureCommand = configureCommandTemplate % d
        print(fullConfigureCommand)
        print("...")

        result = 1
        filePath = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        os.chdir(build_dir)
        try:
            result = check_call(fullConfigureCommand, shell=False)
        except:
            pass
        os.chdir(filePath)

        if result != 0:
            print("########################")
            print("ERROR CONFIGURING CMAKE")
            print("CMake Gui is opened. Try to generate the project and close the cmake gui again.")
            cmake_gui = self.__clearPath(os.path.join(os.path.dirname(cmake_dict["cmake_executable"]), "cmake-gui.exe"))
            call("%(cmake_gui_executable)s %(build_dir)s" % d)

        return result

    def generateCMakeDict(self) -> dict:
        """Generate CMake config as a dict with paths for 3rdParties

        Returns:
            dict: CMake config
        """
        generator = "Visual Studio 17"
        arch = "x64"

        supportedLanguages = ["de"]

        if self.config["cmake_dir"] and os.path.exists(self.config["cmake_dir"]):
            cmakePath = self.config["cmake_dir"]
        else:
            cmakePath = self.__clearPath("..\\3rdParty\\CMake3.29.5\\bin\\CMake.exe")
            self.config["cmake_dir"] = cmakePath
            self.saveConfig()

        openCVPath = self.__clearPath("..\\3rdParty\\OpenCV4.9.0")

        openCVBinDir = self.__clearPath("..\\3rdParty\\OpenCV4.9.0\\x64\\vc17\\bin")
        qmakePath = self.__clearPath("..\\3rdParty\\Qt6.7\\6.7.1\\msvc2019_64\\bin")
        qtBinDir = self.__clearPath("..\\3rdParty\\Qt6.7\\6.7.1\\msvc2019_64\\bin")
        qtPrefixDir = self.__clearPath("..\\3rdParty\\Qt6.7\\6.7.1\\msvc2019_64")
        qtBuildVersion = "Qt6"
        pythonExecPath = self.__clearPath(sys.executable)
        pythonPath = self.__clearPath(os.path.dirname(sys.executable))
        pythonRootDir = self.__clearPath(pythonPath)

        if self.config["build_with_pcl"] is None:
            self.askForPCL()

        if self.config["build_with_pcl"] == "TRUE":
            pclDir = self.__clearPath("..\\3rdPartyPCL\\pcl1.13.0")
            pclBinDir = self.__clearPath("..\\3rdPartyPCL\\pcl1.13.0\\bin")
            vtkDir = self.__clearPath("..\\3rdPartyPCL\\VTK9.2.2\\lib\\cmake\\vtk-9.2")
            vtkBinaries = self.__clearPath("..\\3rdPartyPCL\\VTK9.2.2\\bin")
            eigenIncludeDir = self.__clearPath("..\\3rdPartyPCL\\Eigen3.4.0")
            flannRoot = self.__clearPath("..\\3rdPartyPCL\\flann1.9.1")
            flannIncludeDir = os.path.join(flannRoot, "include")
            flannLibrary = os.path.join(flannRoot, "lib\\flann_cpp_s.lib")
            flannLibraryDebug = os.path.join(flannRoot, "lib\\flann_cpp_s-gd.lib")
            boostIncludeDir = self.__clearPath("..\\3rdPartyPCL\\boost1.78.0")
            qHullIncludeDir = self.__clearPath("..\\3rdPartyPCL\\QHull2020.2\\include")
            qHullLibraryDir = self.__clearPath("..\\3rdPartyPCL\\QHull2020.2\\lib\\qhullstatic.lib")
            qHullLibraryDirDebug = self.__clearPath("..\\3rdPartyPCL\\QHull2020.2\\lib\\qhullstatic_d.lib")
        else:
            pclDir = ""
            pclBinDir = ""
            vtkDir = ""
            vtkBinaries = ""
            eigenIncludeDir = ""
            flannRoot = ""
            flannIncludeDir = ""
            flannLibrary = ""
            flannLibraryDebug = ""
            boostIncludeDir = ""
            qHullIncludeDir = ""
            qHullLibraryDir = ""
            qHullLibraryDirDebug = ""

        cmake_dict = {}
        cmake_dict["build64"] = "TRUE"
        cmake_dict["build_qtversion"] = qtBuildVersion
        cmake_dict["cmake_executable"] = cmakePath
        cmake_dict["itom_languages"] = ",".join(supportedLanguages)
        cmake_dict["qt_prefix_dir"] = qtPrefixDir
        cmake_dict["qt_bin_dir"] = qtBinDir
        cmake_dict["generator"] = generator
        cmake_dict["arch"] = arch
        cmake_dict["opencv_dir"] = openCVPath
        cmake_dict["opencv_bin_dir"] = openCVBinDir
        cmake_dict["qmake_dir"] = qmakePath
        cmake_dict["python_executable"] = pythonExecPath
        cmake_dict["python_root_dir"] = pythonRootDir
        cmake_dict["cmake_gui_executable"] = self.__clearPath(os.path.join(os.path.dirname(cmakePath), "cmake-gui.exe"))
        cmake_dict["build_with_pcl"] = self.config["build_with_pcl"]
        cmake_dict["pcl_dir"] = pclDir
        cmake_dict["pcl_bin_dir"] = pclBinDir
        cmake_dict["vtk_dir"] = vtkDir
        cmake_dict["vtk_bin_dir"] = vtkBinaries
        cmake_dict["boost_include_dir"] = boostIncludeDir
        cmake_dict["eigen_include_dir"] = eigenIncludeDir
        cmake_dict["flann_root"] = flannRoot
        cmake_dict["flann_include_dir"] = flannIncludeDir
        cmake_dict["flann_library"] = flannLibrary
        cmake_dict["flann_library_debug"] = flannLibraryDebug
        cmake_dict["qhull_include_dir"] = qHullIncludeDir
        cmake_dict["qhull_library_dir"] = qHullLibraryDir
        cmake_dict["qhull_library_dir_debug"] = qHullLibraryDirDebug

        return cmake_dict

    def compileDebugAndRelease(self, build_dir: str, project_name: str):
        """Compile VS project in debug ans release

        Args:
            build_dir (str): Build dir containing *.sln
            project_name (str): Project name
        """
        file = os.path.join(build_dir, "compile_debug_and_release.bat")

        content = \
r"""if "%VSWHERE%"=="" set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\\vswhere.exe"
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath`) do (set InstallDir=%%i)
CALL "%InstallDir%\Common7\Tools\VsDevCmd.bat"
msbuild.exe %~dp0\ALL_BUILD.vcxproj /p:configuration=debug /p:platform=x64
CALL "%InstallDir%\Common7\Tools\VsDevCmd.bat"
msbuild.exe %~dp0\ALL_BUILD.vcxproj /p:configuration=release /p:platform=x64
"""

        with open(file, mode="wt") as fp:
            fp.write(content)

        print("Start compiling", project_name, "in debug and release...")
        p = subprocess.Popen(file, shell=False)
        stdout, stderr = p.communicate()
        print(p)
        print("...compiling in debug and release finished")

        return

    def showEnverText(self):
        """save env variables to file"""

        d = self.generateCMakeDict()
        pyPath = "/".join(os.path.dirname(d["python_executable"]).split("\\"))
        text = d["qt_bin_dir"] + ";" + d["opencv_bin_dir"] + ";" + pyPath + ";" + pyPath + "/Scripts" + ";"
        if d["pcl_bin_dir"] != "":
            text += d["pcl_bin_dir"] + ";"
            text += d["vtk_bin_dir"] + ";"

        if platform.release() == "10":
            text = text.replace("/", "\\")

        print("-------------------------------------------------------")
        print("Please prepend the following text to the path environment variable and re-login to your computer:")
        print(" ")
        print(text)
        print("-------------------------------------------------------")
        print("The text is also saved in the file enver.txt (folder __install__).")
        print("-------------------------------------------------------")

        with open(self.__currentDir + "\\enver.txt", "w") as fp:
            fp.write(text)

        return

    def userInput(self):
        """Main user input function"""
        selected = "0"
        self.getStatus()

        defaultStatusString = "(--)"
        okStatusString = "(OK)"

        git_clone_text = defaultStatusString
        itom_cmake_text = defaultStatusString
        plugins_cmake_text = defaultStatusString
        itom_compile_text = defaultStatusString
        plugins_compile_text = defaultStatusString

        print("")
        print(" Python required package versions:")
        print("---------------------------------------")
        print("    updated pip        : {}".format(pip.__version__))
        print("    installed numpy    : {}".format(numpy.__version__))
        print("    installed jedi     : {}".format(jedi.__version__))
        print("    installed flake8   : {}".format(flake8.__version__))
        print("")
        print("")

        while selected != "-1":
            self.getStatus()
            if (
                self.status["itomGitCloned"]
                and self.status["pluginGitCloned"]
                and self.status["designerPluginGitCloned"]
            ):
                git_clone_text = okStatusString

            if self.status["itomCMake"]:
                itom_cmake_text = okStatusString
            if self.status["itomCompiled"]:
                itom_compile_text = okStatusString
            if self.status["pluginCMake"] and self.status["designerPluginCMake"]:
                plugins_cmake_text = okStatusString
            if self.status["itomCompiled"]:
                itom_compile_text = okStatusString
            if self.status["pluginsCompiled"] and self.status["designerpluginsCompiled"]:
                plugins_compile_text = okStatusString

            print(" Select the step you want to execute:")
            print("---------------------------------------")
            print("    1 {}: clone git repositories".format(git_clone_text))
            print("    2 {}: configure and generate CMake (itom base)".format(itom_cmake_text))
            print(
                "    3 {}: compile itom base in Debug and Release (necessary for further steps)".format(
                    itom_compile_text
                )
            )
            print("    4 {}: configure and generate CMake (plugins and designer plugins)".format(plugins_cmake_text))
            print("    5 {}: compile plugins and designer plugins in Debug and Release".format(plugins_compile_text))
            print("    6: Prepend Qt, OpenCV and optionally PCL to PATH variable")
            print("")
            print("    A: execute all steps")
            print("    -1: EXIT")
            print("---------------------------------------")

            selected = input("your input? ")

            try:
                match selected:
                    case "1":
                        self.cloneGit()
                    case "2":
                        self.runCMakeItom()
                    case "3":
                        self.compileDebugAndRelease((self.__currentDir + "\\..\\build\\itom"), "itom")
                    case "4":
                        self.runCMakePlugins()
                    case "5":
                        self.compileDebugAndRelease((self.__currentDir + "\\..\\build\\plugins"), "plugins")
                        self.compileDebugAndRelease(
                            (self.__currentDir + "\\..\\build\\designerplugins"), "designerplugins"
                        )
                    case "6":
                        self.showEnverText()
                    case "A":
                        self.cloneGit()
                        self.runCMakeItom()
                        self.compileDebugAndRelease((self.__currentDir + "\\..\\build\\itom"), "itom")
                        self.runCMakePlugins()
                        self.compileDebugAndRelease((self.__currentDir + "\\..\\build\\plugins"), "plugins")
                        self.compileDebugAndRelease(
                            (self.__currentDir + "\\..\\build\\designerplugins"), "designerplugins"
                        )
                        self.showEnverText()
                    case "-1":
                        print("exit")
                        break

            except Exception as ex:
                print("ERROR: ", ex)
                print("Exception in user code:")
                print("-" * 60)
                traceback.print_exc(file=sys.stdout)
                print("-" * 60)
        return


# -----------------------------
if __name__ == "__main__":
    Main()
