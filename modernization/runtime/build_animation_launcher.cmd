@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
rc /nologo /fo"D:\Games\Magic&Mayham\modernization\build\repath_animation.res" "D:\Games\Magic&Mayham\modernization\runtime\repath_debug.rc"
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER "D:\Games\Magic&Mayham\modernization\runtime\repath_debug_launcher.cpp" "D:\Games\Magic&Mayham\modernization\build\repath_animation.res" /Fo"D:\Games\Magic&Mayham\modernization\build\repath_animation_launcher.obj" /link /SUBSYSTEM:WINDOWS /OUT:"D:\Games\Magic&Mayham\modernization\build\Chaos-Repath-Animation-Trial.exe" bcrypt.lib user32.lib
exit /b %errorlevel%
