TITLE %~dp0 INSTALL ITOM DEVELOPMENT ENVIRONMENT

@echo off
set setupScriptName=setupScript.py
set setupScriptPath=https://raw.githubusercontent.com/itom-project/all-in-one-build-environment/main/x64/MSVC2019_Qt5.15.2/_install_/%setupScriptName%

echo ---------------------------------------------
echo -- STEP 1: Setup script: check for updates --
echo ---------------------------------------------

if exist %~dp0%setupScriptName% (
    echo The main installation script %setupScriptName% already exists.
    echo If desired, it can again be downloaded from 
    echo %setupScriptPath% 
    echo and copied to this directory to ensure the latest version.
    goto ask_download_option
) else (
    echo The main installation script %setupScriptName% does not exist.
    echo It will be downloaded from 
    echo %setupScriptPath% 
    echo and copied to this directory.
    goto download_file
)

:ask_download_option
rem choice command must be outside of if block
choice /M "Should the file be downloaded to get the latest version before executing it (recommended)?"
if %ERRORLEVEL% == 1 (goto download_file)
goto continue_process

:download_file
echo download file
curl -f -o %setupScriptName% -H "Cache-Control: no-cache, no-store" %setupScriptPath%

if %ERRORLEVEL% NEQ 0 (
    echo "The file 
    echo %setupScriptPath% 
    echo could not be downloaded.
    echo Please retry  or copy it manually to this directory and restart.
    goto end
)

:continue_process   

echo ----------------------------------------------------------
echo -- STEP 2: Update Python and install packages           --
echo ----------------------------------------------------------

@echo on
%~dp0..\3rdParty\Python\python.exe -m pip install --upgrade pip%*
%~dp0..\3rdParty\Python\python.exe -m pip install -r requirements.txt%*

@echo off
echo ----------------------------------------------------------
echo -- STEP 3: Run the setup script                         --
echo ----------------------------------------------------------

@echo on
%~dp0..\3rdParty\Python\python.exe %~dp0/%setupScriptName% %*

:end


pause
