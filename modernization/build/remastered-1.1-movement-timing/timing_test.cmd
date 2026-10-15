@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
cl /nologo /O2 /EHsc /std:c++17 /I. "../../tests/movement_timing_test.cpp" /link /OUT:movement_timing_test.exe
if errorlevel 1 exit /b 1
movement_timing_test.exe
