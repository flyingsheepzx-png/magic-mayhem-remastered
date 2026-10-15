@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /EHsc /std:c++17 verify_policy.cpp /link /OUT:verify_policy.exe
