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

__version__ = "1.0.2"

# -------------------------------------------
class Main:
    def __init__(self):
        """ """
        # private members
        self.__settingsFileName = "setup_settings.txt"
        self.__currentDir = os.path.realpath(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))

        # public members
        self.itomProjectSourcePath = self.__clearPath("..\\itomProject")
        self.itomProjectBuildPath = self.__clearPath("..\\itomProject\\build")
        self.config = {"git_path": None, "build_with_pcl": None, "cmake_dir": None}
        self.status = {
            "pipUpgraded": False,
            "numpyInstalled": False,
            "jediInstalled": False,
            "pyflakesInstalled": False,
            "numpyVersionHigher": False,
            "itomProjectGitCloned": False,
            "itomCoreCMake" : False,
            "itomCoreCompiled" : False,
            "PluginsAndDesignerPluginsCmake" : False,
            "PluginsAndDesignerPluginsCompiled" : False
        }
        self.build_itom_core = "OFF"
        self.build_itom_plugins = "OFF"
        self.build_itom_designerplugins = "OFF"

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
        
        return

    def getStatus(self):
        """Get the status of the all in one build steps"""
        # status of git clone
        if os.path.exists(os.path.join(self.itomProjectSourcePath, ".git")):
            self.status["itomProjectGitCloned"] = True

        # status of VS build
        if os.path.exists(os.path.join(self.itomProjectBuildPath, "itom", "ALL_BUILD.vcxproj")):
            self.status["itomCoreCMake"] = True
        if os.path.exists(os.path.join(self.itomProjectBuildPath, "itom", "qitom.exe")) and os.path.exists(os.path.join(self.itomProjectBuildPath, "itom", "qitomd.exe")):
            self.status["itomCoreCompiled"] = True
            
        if os.path.exists(os.path.join(self.itomProjectBuildPath, "plugins", "ALL_BUILD.vcxproj")) and os.path.exists(os.path.join(self.itomProjectBuildPath, "designerplugins", "ALL_BUILD.vcxproj")):
            self.status["PluginsAndDesignerPluginsCmake"] = True
        if self.check_PluginsAndDesignerPluginsCompiled(os.path.join(self.itomProjectBuildPath, "plugins")) and self.check_PluginsAndDesignerPluginsCompiled(os.path.join(self.itomProjectBuildPath, "designerplugins")):
            self.status["PluginsAndDesignerPluginsCompiled"] = True

        return

    def check_PluginsAndDesignerPluginsCompiled(self, main_folder):
        # check if all subfolders except for CmakeFiles and x64 contain a Debug and Release folder
        subdirsexsit = False

        if os.path.exists(os.path.join(self.itomProjectBuildPath, "plugins")) and os.path.exists(os.path.join(self.itomProjectBuildPath, "designerplugins")):

            subfolders = [f.path for f in os.scandir(main_folder) if f.is_dir()]

            subfolders = [f for f in subfolders if os.path.basename(f) != 'CMakeFiles' and os.path.basename(f) != 'x64']

            # Check for Debug and Release in each subfolder
            retVal = 0
            for subfolder in subfolders:
                retVal += not(os.path.isdir(os.path.join(subfolder, 'Debug')))
                retVal += not(os.path.isdir(os.path.join(subfolder, 'Release')))
            subdirsexsit = True if retVal == 0 else False

        else:
            subdirsexsit = False

        return subdirsexsit


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
                [winreg.HKEY_CURRENT_USER, "Software\\Git-Cheetah", "PathToMsys"],
                [winreg.HKEY_LOCAL_MACHINE, "Software\\Git-Cheetah", "PathToMsys"],
                [winreg.HKEY_CURRENT_USER, "Software\\GitForWindows", "InstallPath"],
                [winreg.HKEY_LOCAL_MACHINE, "Software\\GitForWindows", "InstallPath"],
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
        # clone itomProject
        git = self.config["git_path"]
        if git is None:
            self.askForGit()
            self.loadConfig()
            git = self.config["git_path"]
        if os.path.exists(self.__currentDir + "..\\itomProject"):
            raise RuntimeError("The folder '../itomProject' does already exist. Delete it first.")
        
        call(f"{git} clone --recursive https://github.com/itom-project/itomProject.git {self.__currentDir + "\\..\\itomProject"}")
        os.chdir("itomProject")
        call(f"{git} submodule foreach --recursive git checkout master")        
        return
    
    def runCmakeItomProject(self):
        """run cmake for itom project"""
        if not os.path.exists(self.itomProjectBuildPath):
            self.__mkdir_recursive(self.itomProjectBuildPath)

        return self.configureItomProject(self.itomProjectSourcePath, self.itomProjectBuildPath, self.generateCMakeDict())
        
    def configureItomProject(self, source_dir: str, build_dir: str, cmake_dict: dict) -> int:
        """Configure itom project solution

        Args:
            source_dir (str): Git repo source dir
            build_dir (str): build dir
            cmake_dict (dict): CMake config as dict

        Returns:
            int: Result of executing CMake generation
        """
        #+ '-DCONSIDER_GIT_SVN:BOOL=FALSE
        configureCommandTemplate = (
            '%(cmake_executable)s -G "%(generator)s" -A "%(arch)s" -DITOM_LANGUAGES:STRING=%(itom_languages)s -DOpenCV_DIR:PATH="%(opencv_dir)s" -DBUILD_WITH_PCL:BOOL=%(build_with_pcl)s -DBUILD_QTVERSION:STRING=%(build_qtversion)s '
            + '-DQT_QMAKE_EXECUTABLE:FILEPATH="%(qmake_dir)s" -DBUILD_TARGET64:BOOL=TRUE -DPython_ROOT_DIR:FILEPATH="%(python_root_dir)s" '
            + '-DCONSIDER_GIT_SVN:BOOL=TRUE -DPREFER_GIT:BOOL=TRUE "%(source_dir)s" '
            + '-DQt_Prefix_DIR:PATH="%(qt_prefix_dir)s" -DPCL_DIR:PATH="%(pcl_dir)s" -DBoost_USE_STATIC_LIBS:BOOL=ON -DVTK_DIR:PATH="%(vtk_dir)s" '
            + '-DBoost_INCLUDE_DIR:PATH="%(boost_include_dir)s" -DEIGEN_ROOT:PATH="%(eigen_root)s" '
            + '-DFLANN_ROOT:PATH="%(flann_root)s" '
            + '-DQHULL_ROOT:PATH="%(qhull_root)s" '
            + '-DLibUSB_DIR:PATH="%(libusb_include_dir)s" '
            + '-DBUILD_ITOM_CORE:BOOL=%(build_itom_core)s -DBUILD_ITOM_DESIGNERPLUGINS:BOOL=%(build_itom_designerplugins)s -DBUILD_ITOM_PLUGINS:BOOL=%(build_itom_plugins)s '
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
        #except:
        #    pass
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

    def generateCMakeDict(self) -> dict:
        """Generate CMake config as a dict with paths for 3rdParties

        Returns:
            dict: CMake config
        """
        generator = "Visual Studio 16"
        arch = "x64"

        supportedLanguages = ["de"]

        if self.config["cmake_dir"] and os.path.exists(self.config["cmake_dir"]):
            cmakePath = self.config["cmake_dir"]
        else:
            cmakePath = self.__clearPath("..\\3rdParty\\CMake-3.29.5\\bin\\cmake.exe")
            self.config["cmake_dir"] = cmakePath
            self.saveConfig()

        libusbDir = self.__clearPath("..\\3rdParty\\libusb-1.0.27")
        openCVPath = self.__clearPath("..\\3rdParty\\OpenCV4.10.0")
        openCVBinDir = self.__clearPath("..\\3rdParty\\OpenCV4.10.0\\x64\\vc16\\bin")
        qmakePath = self.__clearPath("..\\3rdParty\\Qt5.15.2\\5.15.2\\msvc2019_64\\bin")
        qtBinDir = self.__clearPath("..\\3rdParty\\Qt5.15.2\\5.15.2\\msvc2019_64\\bin")
        qtPrefixDir = self.__clearPath("..\\3rdParty\\Qt5.15.2\\5.15.2\\msvc2019_64")
        qtBuildVersion = "Qt5"
        pythonExecPath = self.__clearPath(sys.executable)
        pythonPath = self.__clearPath(os.path.dirname(sys.executable))
        pythonRootDir = self.__clearPath(pythonPath)

        if self.config["build_with_pcl"] is None:
            self.askForPCL()

        if self.config["build_with_pcl"] == "TRUE":
            pclDir = self.__clearPath("..\\3rdPartyPCL\\pcl1.12.0")
            pclBinDir = self.__clearPath("..\\3rdPartyPCL\\pcl1.12.0\\bin")
            vtkDir = self.__clearPath("..\\3rdPartyPCL\\VTK9.0.3\\lib\\cmake\\vtk-9.0")
            vtkBinaries = self.__clearPath("..\\3rdPartyPCL\\VTK9.0.3\\bin")
            eigenRoot = self.__clearPath("..\\3rdPartyPCL\\Eigen3.4.0")
            flannRoot = self.__clearPath("..\\3rdPartyPCL\\flann1.9.1")
            boostIncludeDir = self.__clearPath("..\\3rdPartyPCL\\boost1.77.0")
            qHullRoot = self.__clearPath("..\\3rdPartyPCL\\QHull2020.2")

        else:
            pclDir = ""
            pclBinDir = ""
            vtkDir = ""
            vtkBinaries = ""
            eigenRoot = ""
            flannRoot = ""
            boostIncludeDir = ""
            qHullRoot = ""

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
        cmake_dict["eigen_root"] = eigenRoot
        cmake_dict["flann_root"] = flannRoot
        cmake_dict["qhull_root"] = qHullRoot
        cmake_dict["libusb_include_dir"] = libusbDir
        cmake_dict["build_itom_core"] = self.build_itom_core
        cmake_dict["build_itom_designerplugins"] = self.build_itom_designerplugins
        cmake_dict["build_itom_plugins"] = self.build_itom_plugins

        return cmake_dict

    def compileDebugAndRelease(self, build_dir: str, project_name: str):
        """Compile VS project in debug ans release

        Args:
            build_dir (str): Build dir containing *.sln
            project_name (str): Project name
        """
        file = os.path.join(build_dir, "compile_debug_and_release.bat")

        content = (
            'if "%VSWHERE%"=="" set "VSWHERE=%ProgramFiles(x86)%\\Microsoft Visual Studio\\Installer\\vswhere.exe" \n'
            + 'for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath`) do (set InstallDir=%%i) \n'
            + 'CALL "%InstallDir%\\Common7\\Tools\\VsDevCmd.bat" \n'
            + "msbuild.exe %~dp0\\ALL_BUILD.vcxproj /p:configuration=debug /p:platform=x64 \n"
            + 'CALL "%InstallDir%\\Common7\\Tools\\VsDevCmd.bat" \n'
            + "msbuild.exe %~dp0\\ALL_BUILD.vcxproj /p:configuration=release /p:platform=x64"
        )  # \n PAUSE"

        with open(file, mode="w") as fp:
            fp.write(content)

        print("Start compiling", project_name, "in debug and release...")
        p = subprocess.Popen(file, shell=False)
        stdout, stderr = p.communicate()
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
        itom_core_cmake_text = defaultStatusString
        itom_core_compile_text = defaultStatusString
        plugins_and_designer_plugins_cmake_text = defaultStatusString
        plugins_and_designer_plugins_compile_text = defaultStatusString

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
            if (self.status["itomProjectGitCloned"]):
                git_clone_text = okStatusString
            if self.status["itomCoreCMake"]:
                itom_core_cmake_text = okStatusString
            if self.status["itomCoreCompiled"]:
                itom_core_compile_text = okStatusString
            if self.status["PluginsAndDesignerPluginsCmake"]:
                plugins_and_designer_plugins_cmake_text = okStatusString
            if self.status["PluginsAndDesignerPluginsCompiled"]:
                plugins_and_designer_plugins_compile_text = okStatusString
            

            print(" Select the step you want to execute:")
            print("---------------------------------------")
            print("    1 {}: clone git repositories".format(git_clone_text))
            print("    2 {}: configure and generate CMake (itom base)".format(itom_core_cmake_text))
            print("    3 {}: compile itom base in Debug and Release (necessary for further steps)".format(itom_core_compile_text))
            print("    4 {}: configure and generate CMake (plugins and designer plugins)".format(plugins_and_designer_plugins_cmake_text))
            print("    5 {}: compile plugins and designer plugins in Debug and Release".format(plugins_and_designer_plugins_compile_text))
            print("    6: Prepend Qt, OpenCV and optionally PCL to PATH variable")
            print("")
            print("    A: execute all steps")
            print("    -1: EXIT")
            print("---------------------------------------")

            selected = input("your input? ")

            try:
                if selected == "1":
                    self.cloneGit()
                elif selected == "2":
                    self.build_itom_core = "ON"
                    self.build_itom_designerplugins = "OFF"
                    self.build_itom_plugins = "OFF"
                    self.runCmakeItomProject()
                elif selected == "3":
                    self.compileDebugAndRelease((self.__currentDir + "\\..\\itomProject\\build\\itom"), "itom")
                elif selected == "4":
                    self.build_itom_core = "OFF"
                    self.build_itom_designerplugins = "ON"
                    self.build_itom_plugins = "ON"
                    self.runCmakeItomProject()
                elif selected == "5":
                    self.compileDebugAndRelease((self.__currentDir + "\\..\\itomProject\\build\\designerplugins"), "designerplugins")
                    self.compileDebugAndRelease((self.__currentDir + "\\..\\itomProject\\build\\plugins"), "plugins")
                elif selected == "6":
                    self.showEnverText()
                elif selected == "A":
                    #self.cloneGit()
                    self.build_itom_core = "ON"
                    self.build_itom_designerplugins = "ON"
                    self.build_itom_plugins = "ON"
                    self.runCmakeItomProject()
                    self.compileDebugAndRelease((self.__currentDir + "\\..\\itomProject\\build"), "itomProject")
                    self.showEnverText()
                elif selected == "-1":
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
