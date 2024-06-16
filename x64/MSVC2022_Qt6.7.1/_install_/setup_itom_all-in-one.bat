TITLE %~dp0 INSTALL ITOM DEVELOPMENT ENVIORNMENT

%~dp0..\3rdParty\Python\python.exe -m pip install --upgrade pip%*
%~dp0..\3rdParty\Python\python.exe -m pip install -r requirements.txt%*

set setupScriptPath=https://raw.githubusercontent.com/itom-project/all-in-one-build-setup/main/README.md


%~dp0..\3rdParty\Python\python.exe %~dp0/setupScript.py %*

pause