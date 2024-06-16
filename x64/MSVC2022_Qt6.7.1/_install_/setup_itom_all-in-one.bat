TITLE %~dp0 INSTALL ITOM DEVELOPMENT ENVIORNMENT

%~dp0..\3rdParty\Python\python.exe -m pip install --upgrade pip%*
%~dp0..\3rdParty\Python\python.exe -m pip install -r requirements.txt%*

@echo off
set setupScriptName=setupScript.py
set setupScriptPath=https://raw.githubusercontent.com/itom-project/all-in-one-build-setup/main/x64/MSVC2022_Qt6.7.1/_install_/%setupScriptName%

echo --------------------------------------------------
echo -- Check, download and execute the setup script --
echo --------------------------------------------------

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
goto start_script

:download_file
echo download file
curl -f -o %setupScriptName% %setupScriptPath%

if %ERRORLEVEL% NEQ 0 (
    echo "The file 
    echo %setupScriptPath% 
    echo could not be downloaded.
    echo Please retry  or copy it manually to this directory and restart.
    goto end
)

:start_script   
@echo on
%~dp0..\3rdParty\Python\python.exe %~dp0/%setupScriptName% %*

:end


pause