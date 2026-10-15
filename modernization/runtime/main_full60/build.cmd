@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
rc /nologo /fo"..\..\build\main_full60.res" "main_full60.rc"
if errorlevel 1 (popd & exit /b 1)
cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER "launcher.cpp" "..\..\build\main_full60.res" /Fo"..\..\build\main_full60_launcher.obj" /link /SUBSYSTEM:WINDOWS /OUT:"..\..\build\Chaos-Main-Full60.exe" bcrypt.lib user32.lib
set result=%errorlevel%
popd
exit /b %result%
