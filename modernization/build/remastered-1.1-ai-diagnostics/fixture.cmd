@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /std:c++17 /DMM_AI_TEST ai_diagnostics.cpp /link /OUT:ai_fixture.dll bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 ai_diagnostics_fp_test.cpp /link /OUT:ai_diagnostics_fp_test.exe
if errorlevel 1 exit /b 1
ai_diagnostics_fp_test.exe
