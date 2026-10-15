@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
cl /nologo /O2 /EHsc /std:c++17 /I"D:\Games\Magic&Mayham\modernization\runtime\hd11" display_test.cpp /link /OUT:display_test.exe
if errorlevel 1 exit /b 1
display_test.exe
