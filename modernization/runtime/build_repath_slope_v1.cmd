@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /W4 "D:\Games\Magic&Mayham\modernization\runtime\releases\repath_slope_v1.cpp" /Fo"D:\Games\Magic&Mayham\modernization\build\repath_slope_v1.obj" /link /OUT:"D:\Games\Magic&Mayham\modernization\build\repath_slope_v1.dll"
if errorlevel 1 exit /b 1
python "D:\Games\Magic&Mayham\modernization\runtime\releases\verify_slope_v1_build.py" "D:\Games\Magic&Mayham\modernization\build\repath_slope_v1.dll"
exit /b %errorlevel%
